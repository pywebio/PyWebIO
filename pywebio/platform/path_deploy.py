import os.path
from functools import partial

import tornado
from tornado import template
from tornado.web import HTTPError, Finish
from tornado.web import StaticFileHandler

from . import utils
from .httpbased import HttpHandler
from .tornado import webio_handler, set_ioloop
from .tornado_http import TornadoHttpContext
from .utils import cdn_validation, make_applications
from ..session import register_session_implement, CoroutineBasedSession, ThreadBasedSession
from ..utils import get_free_port, STATIC_PATH, parse_file_size


def filename_ok(f):
    return not f.startswith(('.', '_'))


def valid_and_norm_path(base, subpath):
    """
    :param str base: MUST a absolute path
    :param str subpath:
    :return: Normalize path. None returned if the sub path is not valid
    """
    subpath = subpath.lstrip('/')
    full_path = os.path.normpath(os.path.join(base, subpath))
    if not full_path.startswith(base):
        return None

    parts = subpath.split('/')
    for i in parts:
        if not filename_ok(i):
            return None

    return full_path


_cached_modules = {}


def _get_module(path, reload=False):
    # Credit: https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path

    global _cached_modules
    import importlib.util

    if not reload and path in _cached_modules:
        return _cached_modules[path]

    # import_name will be the `__name__` of the imported module
    import_name = "__pywebio__"
    spec = importlib.util.spec_from_file_location(import_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _cached_modules[path] = module
    return module


_app_list_tpl = template.Template("""
<!DOCTYPE html>
<html lang="">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>{{ title }}</title>
    <meta name="description" content="PyWebIO applications index">
    <style>a{text-decoration:none}</style>
</head>
<body>
<h1>{{ title }}</h1>
<hr>
<pre style="line-height: 1.6em; font-size: 16px;">
{% for f in files %} <a href="{{ f }}">{{ f }}</a>
{% end %}</pre>
<hr>
</body>
</html>
""".strip())


def default_index_page(path, base):
    urlpath = path[len(base):] or '/'
    title = "Index of %s" % urlpath
    dirs = [] if path == base else ['../']
    files = []
    for f in os.listdir(path):
        if not filename_ok(f):
            continue
        if os.path.isfile(os.path.join(path, f)):
            if f.endswith('.py'):
                files.append(f[:-3])
        else:
            dirs.append(f + '/')
    return _app_list_tpl.generate(files=dirs + files, title=title)


def get_app_from_path(request_path, base, index, reload=False):
    """Get PyWebIO app

    :param str request_path: request path
    :param str base: dir base path, MUST a absolute path
    :param callable index:
    :return: ('error', http error code in int) / ('app', pywebio task function) / ('html', Html content in bytes)
    """
    path = valid_and_norm_path(base, request_path)
    if path is None:
        return 'error', 403

    if os.path.isdir(path):
        if not request_path.endswith('/'):
            return 'error', 404

        if os.path.isfile(os.path.join(path, 'index.py')):
            path = os.path.join(path, 'index.py')
        elif index:
            content = index(path)
            return 'html', content
        else:
            return 'error', 404
    else:
        path += '.py'

    if not os.path.isfile(path):
        return 'error', 404

    module = _get_module(path, reload=reload)
    if hasattr(module, 'main'):
        return 'app', make_applications(module.main)

    return 'error', 404


def _path_deploy(base, port=0, host='', static_dir=None, cdn=True, max_payload_size=2 ** 20 * 200,
                 **tornado_app_settings):
    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    tornado_app_settings = {k: v for k, v in tornado_app_settings.items() if v is not None}

    abs_base = os.path.normpath(os.path.abspath(base))

    cdn = cdn_validation(cdn, 'warn', stacklevel=4)  # if CDN is not available, warn user and disable CDN
    cdn_url = '/_pywebio_static/' if not cdn else cdn

    register_session_implement(CoroutineBasedSession)
    register_session_implement(ThreadBasedSession)

    RequestHandler = yield cdn_url, abs_base

    handlers = []
    if static_dir is not None:
        handlers.append((r"/static/(.*)", StaticFileHandler, {"path": static_dir}))
    if not cdn:
        handlers.append((r"/_pywebio_static/(.*)", StaticFileHandler, {"path": STATIC_PATH}))
    handlers.append((r"/.*", RequestHandler))

    print('Listen on %s:%s' % (host or '0.0.0.0', port))

    set_ioloop(tornado.ioloop.IOLoop.current())  # to enable bokeh app
    app = tornado.web.Application(handlers=handlers, **tornado_app_settings)
    app.listen(port, address=host, max_buffer_size=max_payload_size)
    tornado.ioloop.IOLoop.current().start()


def path_deploy(base, port=0, host='',
                index=True, static_dir=None,
                reconnect_timeout=0,
                cdn=True, debug=True,
                allowed_origins=None, check_origin=None,
                max_payload_size='200M',
                **tornado_app_settings):
    """Deploy the PyWebIO applications from a directory.

    The server communicates with the browser using WebSocket protocol.

    :param str base: Base directory to load PyWebIO application.
    :param int port: The port the server listens on.
    :param str host: The host the server listens on.
    :param bool/callable index: Whether to provide a default index page when request a directory, default is ``True``.
       ``index`` also accepts a function to custom index page, which receives the requested directory path as parameter and return HTML content in string.

       You can override the index page by add a `index.py` PyWebIO app file to the directory.
    :param str static_dir: Directory to store the application static files.
       The files in this directory can be accessed via ``http://<host>:<port>/static/files``.
       For example, if there is a ``A/B.jpg`` file in ``http_static_dir`` path,
       it can be accessed via ``http://<host>:<port>/static/A/B.jpg``.
    :param int reconnect_timeout: The client can reconnect to server within ``reconnect_timeout`` seconds after an unexpected disconnection.
       If set to 0 (default), once the client disconnects, the server session will be closed.

    The rest arguments of ``path_deploy()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`
    """

    utils.MAX_PAYLOAD_SIZE = max_payload_size = parse_file_size(max_payload_size)
    tornado_app_settings.setdefault('websocket_max_message_size', max_payload_size)  # Backward compatible
    tornado_app_settings['websocket_max_message_size'] = parse_file_size(tornado_app_settings['websocket_max_message_size'])
    gen = _path_deploy(base, port=port, host=host,
                       static_dir=static_dir,
                       cdn=cdn, debug=debug,
                       max_payload_size=max_payload_size,
                       **tornado_app_settings)

    cdn_url, abs_base = next(gen)

    index_func = {True: partial(default_index_page, base=abs_base), False: lambda p: '403 Forbidden'}.get(index, index)

    Handler = webio_handler(lambda: None, cdn_url, allowed_origins=allowed_origins,
                            check_origin=check_origin, reconnect_timeout=reconnect_timeout)

    class WSHandler(Handler):

        def get_app(self):
            reload = self.get_query_argument('reload', None) is not None
            type, res = get_app_from_path(self.request.path, abs_base, index=index_func, reload=reload)
            if type == 'error':
                raise HTTPError(status_code=res)
            elif type == 'html':
                raise Finish(res)

            app_name = self.get_query_argument('app', 'index')
            app = res.get(app_name) or res['index']

            return app

    gen.send(WSHandler)
    gen.close()


def path_deploy_http(base, port=0, host='',
                     index=True, static_dir=None,
                     cdn=True, debug=True,
                     allowed_origins=None, check_origin=None,
                     session_expire_seconds=None,
                     session_cleanup_interval=None,
                     max_payload_size='200M',
                     **tornado_app_settings):
    """Deploy the PyWebIO applications from a directory.

    The server communicates with the browser using HTTP protocol.

    The ``base``, ``port``, ``host``, ``index``, ``static_dir`` arguments of ``path_deploy_http()``
    have the same meaning as for :func:`pywebio.platform.path_deploy`

    The rest arguments of ``path_deploy_http()`` have the same meaning as for :func:`pywebio.platform.tornado_http.start_server`
    """
    utils.MAX_PAYLOAD_SIZE = max_payload_size = parse_file_size(max_payload_size)

    gen = _path_deploy(base, port=port, host=host,
                       static_dir=static_dir,
                       cdn=cdn, debug=debug,
                       max_payload_size=max_payload_size,
                       **tornado_app_settings)

    cdn_url, abs_base = next(gen)
    index_func = {True: partial(default_index_page, base=abs_base), False: lambda p: '403 Forbidden'}.get(index, index)

    def get_app(context: TornadoHttpContext):
        reload = context.request_url_parameter('reload', None) is not None

        type, res = get_app_from_path(context.get_path(), abs_base, index=index_func, reload=reload)
        if type == 'error':
            raise HTTPError(status_code=res)
        elif type == 'html':
            raise Finish(res)

        app_name = context.request_url_parameter('app', 'index')
        return res.get(app_name) or res['index']

    handler = HttpHandler(app_loader=get_app, cdn=cdn_url,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins,
                          check_origin=check_origin)

    class ReqHandler(tornado.web.RequestHandler):
        def options(self):
            return self.get()

        def post(self):
            return self.get()

        def get(self):
            context = TornadoHttpContext(self)
            self.write(handler.handle_request(context))

    gen.send(ReqHandler)
    gen.close()
