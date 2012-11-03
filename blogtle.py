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
FREEZER_BASE_URL = site['root'].rstrip('/')

PERMALINK_TEMPLATE=site['permalink']

app = Flask(__name__,static_url_path='/',static_folder='static')
app.config.from_object(__name__)
jinja_ext.filter_add(app)

gen_pages = FlatPages(app)
freezer = Freezer(app,log_url_for=False)

post = sorted([page for page in gen_pages.get_pages_by_meta('layout','post')],key=lambda x: x.meta['date'],reverse=True)

@app.route('/')
@app.route('/archives/page/<int:p_num>/')
def index(p_num=1):
  global post_len
  post_len = len(post)
  if p_num < 2:
    prev = None
  elif p_num == 2:
    prev = url_for('index')
  else:
    prev = url_for('index',p_num=p_num-1)
  next = url_for('index',p_num=p_num+1) if p_num < (post_len//site['paginate']+1) else None
  return render_template('index.html', pages=post[site['paginate']*(p_num-1):site['paginate']*p_num],page_prev = prev, page_next=next)

@freezer.register_generator
def index():
  for p_num in range(2,(post_len//site['paginate']+2)):
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
  category = [p for p in post if categories in p.meta['categories']]
  return render_template('categories.html', pages=category, categories=categories)

@freezer.register_generator
def categories():
  for categories in gen_pages.get_categories:
    yield {'categories': categories}

@app.route('/archives/categories/<string:categories>/atom.xml')
def categories_atom(categories):
  category = [p for p in post if categories in p.meta['categories']][0:5]
  response = make_response(render_template('atom.xml', pages=category,categories=categories))
  response.mimetype = 'application/xml'
  return response

@freezer.register_generator
def categories_atom():
  for categories in gen_pages.get_categories:
    yield {'categories': categories}

@app.route('/<path:path>')
def page(path):
  if ('/'+path) in gen_pages.get_all_premalink:
    page = gen_pages.get_all_premalink['/'+path]
    return render_template('page.html', page=page)
  elif ('/'+path+'/') in gen_pages.get_all_premalink:
    page = gen_pages.get_all_premalink['/'+path+'/']
    return render_template('page.html', page=page)
  else:
    return send_from_directory(os.path.join(app.root_path, 'static'),path)

@freezer.register_generator
def page():
  for path in gen_pages.get_all_premalink:
    yield {'path': path }
    
@app.context_processor
def inject_globals():
    return dict(site = site)

@app.route('/sitemap.xml')
def sitemap():
  response = "<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"
  for i in gen_pages.get_all_premalink:
    response += '\t<url>\n'
    response += ('\t\t<loc>'+ site['url'].rstrip('/')+ site['root'].rstrip('/') + '/' + i +'</loc>\n')
    response += '\t\t<lastmod>'+ site['time'].strftime('%Y-%m-%dT%H:%M:%S')+ site['timezone'] +'</lastmod>\n'
    response += '\t</url>\n'
  response += '</urlset>'
  response = make_response(response)
  response.mimetype = 'application/xml'
  return response

def run_app():
  extra_dirs = ['pages',]
  extra_files = extra_dirs[:]
  for extra_dir in extra_dirs:
    for dirname, dirs, files in os.walk(extra_dir):
      for filename in files:
        filename = os.path.join(dirname, filename)
        if os.path.isfile(filename):
          extra_files.append(filename)
  app.run(extra_files=extra_files,debug=True)

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == "build":
    freezer.freeze()
  else:
    run_app()
