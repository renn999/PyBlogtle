from jinja2 import evalcontextfilter, Markup

@evalcontextfilter
def excerpt(ctx,value):
  j=[]
  for i in value.split(u'\n'):
    if i == u'<!--more-->':
      break
    else:
      j = j + [i]
  result = u'\n'.join(j)
  if ctx.autoescape:
    result = Markup(result)
  return result

def has_excerpt(text):
  if u'<!--more-->' in text.split(u'\n'):
    return True
  else:
    return False




