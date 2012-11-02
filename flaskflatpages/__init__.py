# coding: utf8
"""
    flask_flatpages
    ~~~~~~~~~~~~~~~~~~

    Flask-FlatPages provides a collections of pages to your Flask application.
    Pages are built from “flat” text files as opposed to a relational database.

    :copyright: (c) 2010 by Simon Sapin.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement
import sys
import os
import itertools
import datetime

import yaml
import markdown
import werkzeug
import flask

from werkzeug.utils import import_string
from dateutil import parser

sys.path.insert(0, os.path.join(os.getcwd(),'markdown_ext/'))

VERSION = '0.4'


def pygmented_markdown(text):
    """Render Markdown text to HTML. Uses the `Codehilite`_ extension
    if `Pygments`_ is available.

    .. _Codehilite: http://www.freewisdom.org/projects/python-markdown/CodeHilite
    .. _Pygments: http://pygments.org/
    """
    extensions = []
    for i,j,k in os.walk(os.path.join(os.getcwd(),'markdown_ext/')):
        for l in (m for m in k if m.endswith('.py')) :
            try:
                l = l.replace('.py','')
                import_string(l)
            except ImportError:
                extensions = []
            else:
                l = l.replace('mdx_','')
                extensions = extensions + [l]
    md_ext = dict({'codehilite(force_linenos=True)':'pygments','fenced_code':'pygments'})
    for key, value in md_ext.iteritems():
      try:
          import_string(value)
      except ImportError:
          extensions = []
      else:
          extensions = extensions + [key]
    return markdown.markdown(text, extensions)


def pygments_style_defs(style='default'):
    """:return: the CSS definitions for the `Codehilite`_ Markdown plugin.

    :param style: The Pygments `style`_ to use.

    Only available if `Pygments`_ is.

    .. _Codehilite: http://www.freewisdom.org/projects/python-markdown/CodeHilite
    .. _Pygments: http://pygments.org/
    .. _style: http://pygments.org/docs/styles/
    """
    import pygments.formatters
    formater = pygments.formatters.HtmlFormatter(style=style)
    return formater.get_style_defs('.codehilite')


class Page(object):
    def __init__(self, path, meta_yaml, body, html_renderer,permalink_temp):
        #: Path this pages was obtained from, as in ``pages.get(path)``.
        self.path = path
        #: Content of the pages.
        self.body = body
        self._meta_yaml = meta_yaml
        self.html_renderer = html_renderer
        self.permalink_temp = permalink_temp

    def __repr__(self):
        return '<Page %r>' % self.path

    @werkzeug.cached_property
    def html(self):
        """The content of the page, rendered as HTML by the configured renderer.
        """
        return self.html_renderer(self.body)

    def __html__(self):
        """In a template, ``{{ page }}`` is equivalent to
        ``{{ page.html|safe }}``.
        """
        return self.html

    def permalink_gen(self,meta):
        if meta['layout'] != 'page':
            i = meta['date'].strftime('%Y,%m,%d').split(',')
            j = self.permalink_temp.replace(':year',i[0])                 \
                                   .replace(':month',i[1])                \
                                   .replace(':i_month',str(int(i[1])))   \
                                   .replace(':day',i[2])                  \
                                   .replace(':i_day',str(int(i[2])))     \
                                   .replace(':title',meta['title'])       \
                                   .replace(' ','-')
            if not j.endswith('.html') and not j.endswith('/') and not j.endswith('.htm'):
                j=j+'/'
        else:
            j = self.path
        return j

    @werkzeug.cached_property
    def meta(self):
        """A dict of metadata parsed as YAML from the header of the file."""
        meta = yaml.safe_load(self._meta_yaml)
        # YAML documents can be any type but we want a dict
        # eg. yaml.safe_load('') -> None
        #     yaml.safe_load('- 1\n- a') -> [1, 'a']
        if not meta:
            return {}
        if not isinstance(meta, dict):
            raise ValueError("Excpected a dict in metadata for '%s', got %s"
                % (self.path, type(meta).__name__))
        if meta.has_key('date'):
            meta['date'] = parser.parse(meta['date'])
        if meta and not meta.has_key('permalink'):
            meta['permalink'] = self.permalink_gen(meta)
        if not meta['permalink'].endswith('.html') and not meta['permalink'].endswith('/') and not meta['permalink'].endswith('.htm'):
            meta['permalink'] = meta['permalink'] + '/'
        return meta

    def __getitem__(self, name):
        """Shortcut for accessing metadata.

        ``page['title']`` or, in a template, ``{{ page.title }}`` are
        equivalent to ``page.meta['title']``.
        """
        return self.meta[name]
    


class FlatPages(object):
    """
    A collections of :class:`Page` objects.

    :param app: your application. Can be omited if you call
                :meth:`init_app` later.
    :type app: Flask instance

    """
    def __init__(self, app=None):

        #: dict of filename: (page object, mtime when loaded)
        self._file_cache = {}

        if app:
            self.init_app(app)


    def init_app(self, app):
        """ Used to initialize an application, useful for
        passing an app later and app factory patterns.

        :param app: your application
        :type app: Flask instance

        """

        app.config.setdefault('FLATPAGES_ROOT', 'pages')
        app.config.setdefault('FLATPAGES_EXTENSION', '.html')
        app.config.setdefault('FLATPAGES_ENCODING', 'utf8')
        app.config.setdefault('FLATPAGES_HTML_RENDERER', pygmented_markdown)
        app.config.setdefault('FLATPAGES_AUTO_RELOAD', 'if debug')
        app.config.setdefault('PERMALINK_TEMPLATE', '/:year/:month/:day/:title/')

        self.app = app

        app.before_request(self._conditional_auto_reset)

    def _conditional_auto_reset(self):
        """Reset if configured to do so on new requests."""
        auto = self.app.config['FLATPAGES_AUTO_RELOAD']
        if auto == 'if debug':
            auto = self.app.debug
        if auto:
            self.reload()

    def reload(self):
        """Forget all pages.

        All pages will be reloaded next time they're accessed

        """
        try:
            # This will "unshadow" the cached_property.
            # The property will be re-executed on next access.
            del self.__dict__['_pages']
        except KeyError:
            pass

    def __iter__(self):
        """Iterate on all :class:`Page` objects."""
        return self._pages.itervalues()

    def get(self, path, default=None):
        """Returns the :class:`Page` object at ``path``, or ``default``
        if there is no such page.

        """
        # This may trigger the property. Do it outside of the try block.
        pages = self._pages
        try:
            return pages[path]
        except KeyError:
            return default

    
    @property
    def root(self):
        """Full path to the directory where pages are looked for.

        It is the `FLATPAGES_ROOT` config value, interpreted as relative to
        the app root directory.

        """
        return os.path.join(self.app.root_path,
                            self.app.config['FLATPAGES_ROOT'])

    @werkzeug.cached_property
    def _pages(self):
        """Walk the page root directory an return a dict of
        unicode path: page object.

        """
        def _walk(directory, path_prefix=()):
            for i, j, k in os.walk(directory):
                for name in k:
                    full_name = os.path.join(i,name)
                    name_without_extension = name[:-len(extension)]
                    path = u'/'.join((i,) + (name_without_extension,))[len(directory):]
                    pages[path] = self._load_file(path, full_name)

        extension = self.app.config['FLATPAGES_EXTENSION']
        pages = {}
        # Fail if the root is a non-ASCII byte string. Use Unicode.
        _walk(unicode(self.root))
        return pages

    def _load_file(self, path, filename):
        mtime = os.path.getmtime(filename)
        cached = self._file_cache.get(filename)
        if cached and cached[1] == mtime:
            # cached == (page, old_mtime)
            page = cached[0]
        else:
            with open(filename) as fd:
                content = fd.read().decode(
                    self.app.config['FLATPAGES_ENCODING'])
            page = self._parse(content, path)
            self._file_cache[filename] = page, mtime
        return page

    def _parse(self, string, path):
        lines = iter(string.split(u'\n'))
        # Read lines until an empty line is encountered.
        meta = u'\n'.join(itertools.takewhile(unicode.strip, lines))
        # The rest is the content. `lines` is an iterator so it continues
        # where `itertools.takewhile` left it.
        content = u'\n'.join(lines)

        html_renderer = self.app.config['FLATPAGES_HTML_RENDERER']
        permalink_temp = self.app.config['PERMALINK_TEMPLATE']
        if not callable(html_renderer):
            html_renderer = werkzeug.import_string(html_renderer)
        return Page(path, meta, content, html_renderer,permalink_temp)
