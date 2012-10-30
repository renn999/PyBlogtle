import re
import markdown

IMG_RE = re.compile( r'\{\%[ ]*(img)[ ]*(?P<url>.*?)[ ]*\%\}',re.DOTALL)
CODE_WRAP = '<img src=%s />'

class ImgTagExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('imgtag',ImgTagPreprocessor(md),'_begin')
        md.registerExtension(self)

class ImgTagPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self,lines):
        text = []
        for line in lines:
            while 1:
                m = IMG_RE.search(line)
                if m:
                    url = m.group('url')
                    code = CODE_WRAP % url
                    placeholder = self.markdown.htmlStash.store(code, safe=True)
                    line = '%s\n%s\n%s'% (line[:m.start()], placeholder, line[m.end():])
                else:
                    break
            text = text+[line]
        return text

def makeExtension(config=None):
    return ImgTagExtension()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
