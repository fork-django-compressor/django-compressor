import sys

import six
from django.utils.encoding import smart_str

from compressor.exceptions import ParserError
from compressor.parser import ParserBase


# Since Python 3.4, the HTMLParser constructor takes a 'convert_charrefs'
# argument which raises a warning if we don't pass it.
HTML_PARSER_ARGS = {}
if sys.version_info[:2] >= (3, 4):
    HTML_PARSER_ARGS['convert_charrefs'] = False


class DefaultHtmlParser(ParserBase, six.moves.html_parser.HTMLParser):
    def __init__(self, content):
        six.moves.html_parser.HTMLParser.__init__(self, **HTML_PARSER_ARGS)
        self.content = content
        self._css_elems = []
        self._js_elems = []
        self._current_tag = None
        try:
            self.feed(self.content)
            self.close()
        except Exception as err:
            lineno = err.lineno
            line = self.content.splitlines()[lineno]
            raise ParserError("Error while initializing HtmlParser: %s (line: %s)" % (err, repr(line)))

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ('style', 'script'):
            if tag == 'style':
                tags = self._css_elems
            elif tag == 'script':
                tags = self._js_elems
            tags.append({
                'tag': tag,
                'attrs': attrs,
                'attrs_dict': dict(attrs),
                'text': ''
            })
            self._current_tag = tag
        elif tag == 'link':
            self._css_elems.append({
                'tag': tag,
                'attrs': attrs,
                'attrs_dict': dict(attrs),
                'text': None
            })

    def handle_endtag(self, tag):
        if self._current_tag and self._current_tag == tag.lower():
            self._current_tag = None

    def handle_data(self, data):
        if self._current_tag == 'style':
            self._css_elems[-1]['text'] = data
        elif self._current_tag == 'script':
            self._js_elems[-1]['text'] = data

    def css_elems(self):
        return self._css_elems

    def js_elems(self):
        return self._js_elems

    def elem_name(self, elem):
        return elem['tag']

    def elem_attribs(self, elem):
        return elem['attrs_dict']

    def elem_content(self, elem):
        return smart_str(elem['text'])

    def elem_str(self, elem):
        tag = {}
        tag.update(elem)
        tag['attrs'] = ''
        if len(elem['attrs']):
            tag['attrs'] = ' %s' % ' '.join(['%s="%s"' % (name, value) for name, value in elem['attrs']])
        if elem['tag'] == 'link':
            return '<%(tag)s%(attrs)s>' % tag
        else:
            return '<%(tag)s%(attrs)s>%(text)s</%(tag)s>' % tag
