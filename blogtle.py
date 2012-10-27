#!/usr/bin/env python

import sys, os, datetime, yaml,jinja_ext
from flask import Flask, render_template, send_from_directory, make_response, url_for
from flaskflatpages import FlatPages
from flask_frozen import Freezer
#import logging
#logging.basicConfig()

site = yaml.safe_load(open('./_config.yml').read().decode('UTF-8'))
site['time']=datetime.datetime.now()
site['timezone']='+0800'
DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.markdown'
FLATPAGES_MD_OTHER_EXTENTION = {'readmoretag':'mdx_readmoretag','fenced_code':'pygments', \
  'octo_code':'mdx_octo_code','coderehilite':'mdx_coderehilite'}

PERMALINK_TEMPLATE=site['permalink']

app = Flask(__name__,static_url_path='/',static_folder='static')
app.config.from_object(__name__)
jinja_ext.filter_add(app)

pages = FlatPages(app)
freezer = Freezer(app,log_url_for=False)

def permalink_gen(meta):
  i = meta['date'].strftime('%Y,%m,%d').split(',')
  j = PERMALINK_TEMPLATE.replace(':year',i[0]).replace(':month',i[1]).replace(':i_month',str(int(i[1]))).replace(':day',i[2]).replace(':i_day',str(int(i[2]))).replace(':title',meta['title']).replace(' ','-')
  if not j.endswith('.html') and not j.endswith('/') and not j.endswith('.htm'):
    j=j+'/'
  return j

pe_to_pa=dict()
count=0
all_categories=[]

for page in pages:
  if page.meta.has_key('permalink') :
    if not page.meta['permalink'].endswith('.html') and not page.meta['permalink'].endswith('/') and not page.meta['permalink'].endswith('.htm'):
      page.meta['permalink'] = page.meta['permalink'] + '/'
    pe_to_pa[page.meta['permalink'].lstrip('/')] = page
  else:
    if page.meta['layout'] == 'post':
      pl=permalink_gen(page.meta)
      page.meta['permalink'] = pl
      pe_to_pa[pl] = page
    else:
      pe_to_pa[page.path+'/']=page
  count = count + 1
  all_categories = list(set(all_categories + page.meta['categories']))

pages = sorted(pages,key=lambda x: x.meta['date'],reverse=True)
post = [page for page in pages if page.meta['layout']=='post']

@app.route('/')
@app.route('/archives/page/<int:p_num>/')
def index(p_num=1):
  global post
  if p_num < 2:
    prev = None
  elif p_num == 2:
    prev = url_for('index')
  else:
    prev = url_for('index',p_num=p_num-1)
  next = url_for('index',p_num=p_num+1) if p_num < (count//10+1) else None
  return render_template('index.html', pages=post[10*(p_num-1):10*p_num],page_prev = prev, page_next=next)

@freezer.register_generator
def index():
  for p_num in range(2,(count//10+2)):
    yield {'p_num': p_num}

@app.route('/atom.xml')
def atom():
  response = make_response(render_template('atom.xml', pages=post[0:10]))
  response.mimetype = 'application/xml'
  return response

@app.route('/archives/')
def archives():
  archives = 'Blog Archives'
  return render_template('categories.html', pages=post,archives=archives)

@app.route('/archives/categories/<string:categories>/')
def categories(categories):
  category = [p for p in pages if categories in p.meta.get('categories', [])]
  return render_template('categories.html', pages=category, categories=categories)

@freezer.register_generator
def categories():
  for categories in all_categories:
    yield {'categories': categories}

@app.route('/archives/categories/<string:categories>/atom.xml')
def categories_atom(categories):
  category = [p for p in pages if categories in p.meta.get('categories', [])][0:5]
  response = make_response(render_template('atom.xml', pages=category,categories=categories))
  response.mimetype = 'application/xml'
  return response

@freezer.register_generator
def categories_atom():
  for categories in all_categories:
    yield {'categories': categories}

@app.route('/<path:path>')
def page(path):
  if path in pe_to_pa:
    page = pe_to_pa[path]
    return render_template('page.html', page=page)
  else:
    return send_from_directory(os.path.join(app.root_path, 'static'),path)

@freezer.register_generator
def page():
  for path in pe_to_pa.keys():
    yield {'path': path }
    
@app.context_processor
def inject_globals():
    return dict(site = site)

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == "build":
    freezer.freeze()
  else:
    app.run(debug=True)
