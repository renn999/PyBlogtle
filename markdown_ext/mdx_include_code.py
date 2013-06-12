#!/usr/bin/env python

import re, os, sys
import markdown
from markdown.extensions.codehilite import CodeHilite, CodeHiliteExtension
# Global vars
INCLUDE_CODE_RE = re.compile( \
    r'\{\%[ ]*include_code([ ]*lang\:(?P<lang>[a-zA-Z0-9_+-]*))?[ ]*(?P<path>[./_a-zA-Z0-9+-]*?)[ ]*\%\}',
    re.DOTALL)
CODE_WRAP = '<pre><code%s>%s</code></pre>'
LANG_TAG = ' class="%s"'

class IncludeCodeExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        """ Add OctoBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.preprocessors.add('include_code',
                                 IncludeCodePreprocessor(md),
                                 "_begin")


class IncludeCodePreprocessor(markdown.preprocessors.Preprocessor):

    def __init__(self, md):
        markdown.preprocessors.Preprocessor.__init__(self, md)

        self.checked_for_codehilite = False
        self.codehilite_conf = {}

    def run(self, lines):
        """ Match and store Octo Code Blocks in the HtmlStash. """

        # Check for code hilite extension
        if not self.checked_for_codehilite:
            for ext in self.markdown.registeredExtensions:
                if isinstance(ext, CodeHiliteExtension):
                    self.codehilite_conf = ext.config
                    break

            self.checked_for_codehilite = True

        text = "\n".join(lines)
        while 1:
            m = INCLUDE_CODE_RE.search(text)
            if m:
                lang = ''
                if m.group('lang'):
                    lang = LANG_TAG % m.group('lang')
                code_path=os.path.join(os.getcwd(),'static/downloads/code',m.group('path'))
                code = open(code_path,'r').read()
                # If config is not empty, then the codehighlite extension
                # is enabled, so we call it to highlite the code
                if self.codehilite_conf:
                    highliter = CodeHilite(code,
                            linenums=self.codehilite_conf['linenums'][0],
                            guess_lang=self.codehilite_conf['guess_lang'][0],
                            css_class=self.codehilite_conf['css_class'][0],
                            style=self.codehilite_conf['pygments_style'][0],
                            lang=(m.group('lang') or None),
                            noclasses=self.codehilite_conf['noclasses'][0])

                    code = highliter.hilite()
                else:
                    code = CODE_WRAP % (lang, self._escape(code))

                placeholder = self.markdown.htmlStash.store(code, safe=True)
                text = '%s\n%s\n%s'% (text[:m.start()], placeholder, text[m.end():])
            else:
                break
        return text.split("\n")

    def _escape(self, txt):
        """ basic html escaping """
        txt = txt.replace('&', '&amp;')
        txt = txt.replace('<', '&lt;')
        txt = txt.replace('>', '&gt;')
        txt = txt.replace('"', '&quot;')
        return txt


def makeExtension(configs=None):
    return IncludeCodeExtension(configs=configs)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
