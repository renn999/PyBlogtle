#!/usr/bin/env python

import re
import markdown

# Global vars
Octo_BLOCK_RE = re.compile( \
    r'^<table class="codehilitetable"><tr><td class="linenos"><div class="linenodiv"><pre>(?P<line_num>.*)</pre></div></td><td class="code"><div class="codehilite"><pre>(?P<code>.*)</pre></div>',
    re.MULTILINE|re.DOTALL
    )

class coderehiliteExtension(markdown.Extension):

    def extendMarkdown(self, md, md_globals):
        """ Add coderehiliteBlockPreprocessor to the Markdown instance. """
        md.registerExtension(self)

        md.postprocessors.add('coderehilite',
                                 coderehiliteBlockPreprocessor(md),
                                 "_end")


class coderehiliteBlockPreprocessor(markdown.postprocessors.Postprocessor):

    def run(self, text):
        box = []
        j=1
        for i in text.split('</td></tr></table>'):
            while 1:
                m = Octo_BLOCK_RE.search(i)
                if m:
                    num_ln = []
                    for j in m.group('line_num').split('\n'):
                        j = '<span class=\'line-number\'>'+ j + '</span>'
                        num_ln += [j]
                    code_ln=[]
                    for j in m.group('code').split('\n'):
                        j = "<span class='line'>" + j +'</span>'
                        code_ln += [j]
                    placeholder = '<figure class="code"><figcaption><span></span></figcaption><div class="highlight"><table><tr><td class="gutter"><pre class="line-numbers">'+ u'\n'.join(num_ln) + '</pre></td><td class=\'code\'><pre><code>'+u'\n'.join(code_ln)+'</code></pre></td></tr></table></div></figure>'
                    i = '%s\n%s\n%s'% (i[:m.start()], placeholder, i[m.end():])
                else:
                    break
            box = box + [i]
        text = '\n'.join(box)
        return text


def makeExtension(configs=None):
    return coderehiliteExtension(configs=configs)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
