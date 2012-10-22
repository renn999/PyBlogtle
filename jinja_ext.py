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


@evalcontextfilter
def cdata_escape(ctx,value):
  value = value.replace('<![CDATA[', '&lt;![CDATA[').replace(']]>', ']]&gt;')
  if ctx.autoescape:
    value = Markup(value)
  return value

def has_excerpt(text):
  if u'<!--more-->' in text.split(u'\n'):
    return True
  else:
    return False

def filter_add(obj):
  obj.jinja_env.filters['excerpt'] = excerpt
  obj.jinja_env.tests['has_excerpt'] = has_excerpt
  obj.jinja_env.filters['cdata_escape'] = cdata_escape
  
