#!/usr/bin/env python

import sys, os, datetime
from flask import Flask, render_template, send_from_directory
from flaskflatpages import FlatPages
from flask_frozen import Freezer
from dateutil import parser
#import logging
#logging.basicConfig()
import jinja_ext

DEBUG = True
FLATPAGES_AUTO_RELOAD = DEBUG
FLATPAGES_EXTENSION = '.markdown'
FLATPAGES_MD_OTHER_EXTENTION = {'readmoretag':'mdx_readmoretag','fenced_code':'pygments'}

PERMALINK_TEMPLATE=':year-:month-:day-:title'

app = Flask(__name__,static_url_path='/',static_folder='static')
app.config.from_object(__name__)
jinja_ext.filter_add(app)

pages = FlatPages(app)
freezer = Freezer(app)

def permalink_gen(meta):
  i = parser.parse(meta['date'],yearfirst=True).strftime('%Y,%m,%d').split(',')
  j = PERMALINK_TEMPLATE.replace(':year',i[0]).replace(':month',i[1]).replace(':i_month',str(int(i[1]))).replace(':day',i[2]).replace(':i_day',str(int(i[2]))).replace(':title',meta['title']).replace(' ','-')
  if not j.endswith('.html') and not j.endswith('/') and not j.endswith('.htm'):
    j=j+'/'
  return j

pe_to_pa=dict()
count=0
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

@app.route('/')
@app.route('/archives/page/<int:p_num>/')
def index(p_num=1):
  page=sorted(pages,key=lambda x: x.meta['date'],reverse=True)[10*(p_num-1):10*p_num]
  #page=sorted(pages,key=lambda x: x.meta['date'],reverse=True)
  return render_template('index.html', pages=page,p_num=p_num, count=count//10+1)

@app.route('/atom.xml')
def atom():
  page=sorted(pages,key=lambda x: x.meta['date'],reverse=True)[0:20]
  return render_template('atom.xml', pages=page)

@app.route('/categories/<string:categories>/')
def categories(categories):
  category = [p for p in pages if categories in p.meta.get('categories', [])]
  return render_template('categories.html', pages=category, categories=categories)

@app.route('/<path:path>')
def page(path):
  if path in pe_to_pa:
    page = pe_to_pa[path]
    return render_template('page.html', page=page)
  else:
    return send_from_directory(os.path.join(app.root_path, 'static'),path)

@app.context_processor
def inject_globals():
    site = dict()
    site['disqus_short_name'] = 'rennidit'
    site['url']='http://www.renn999.twbbs.org'
    return dict(site = site)

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == "build":
    freezer.freeze()
  else:
    app.run(port=8000)

