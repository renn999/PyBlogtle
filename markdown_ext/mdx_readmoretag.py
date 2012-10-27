import markdown

class ReadMoreTagExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.preprocessors.add('readmoretag',ReadMoreTagPreprocessor(md),'_begin')
        md.registerExtension(self)

class ReadMoreTagPreprocessor(markdown.preprocessors.Preprocessor):
    def run(self,lines):
        text = "\n".join(lines)
        text = text.replace('<!--more-->',"\n\n\n<!--more-->\n\n\n")
        return text.split("\n")

def makeExtension(config=None):
    return ReadMoreTagExtension()

if __name__ == "__main__":
    import doctest
    doctest.testmod()
