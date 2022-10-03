"""
Flask backend
"""
import json
import logging
import os
import threading

import werkzeug
from flask import Flask, request, send_from_directory, Response

from . import page
from .adaptor.http import HttpContext, HttpHandler, run_event_loop
from .page import make_applications
from .remote_access import start_remote_access_service
from .utils import cdn_validation
from ..session import Session
from ..utils import STATIC_PATH, iscoroutinefunction, isgeneratorfunction
from ..utils import get_free_port, parse_file_size

logger = logging.getLogger(__name__)


class FlaskHttpContext(HttpContext):
    backend_name = 'flask'

    def __init__(self):
        self.response = Response()
        self.request_data = request.data

    def request_obj(self):
        """返回当前请求对象"""
        return request._get_current_object()

    def request_method(self):
        """返回当前请求的方法，大写"""
        return request.method

    def request_headers(self):
        """返回当前请求的header字典"""
        return request.headers

    def request_url_parameter(self, name, default=None):
        """返回当前请求的URL参数"""
        return request.args.get(name, default=default)

    def request_body(self):
        return self.request_data

    def set_header(self, name, value):
        """为当前响应设置header"""
        self.response.headers[name] = value

    def set_status(self, status: int):
        """为当前响应设置http status"""
        self.response.status_code = status

    def set_content(self, content, json_type=False):
        """设置相应的内容

        :param content:
        :param bool json_type: content是否要序列化成json格式，并将 content-type 设置为application/json
        """
        # self.response.data accept str and bytes
        if json_type:
            self.set_header('content-type', 'application/json')
            self.response.data = json.dumps(content)
        else:
            self.response.data = content

    def get_response(self):
        """获取当前的响应对象，用于在私图函数中返回"""
        return self.response

    def get_client_ip(self):
        """获取用户的ip"""
        return request.remote_addr


def webio_view(applications, cdn=True,
               session_expire_seconds=None,
               session_cleanup_interval=None,
               allowed_origins=None, check_origin=None):
    """Get the view function for running PyWebIO applications in Flask.
    The view communicates with the browser by HTTP protocol.

    The arguments of ``webio_view()`` have the same meaning as for :func:`pywebio.platform.flask.start_server`
    """

    cdn = cdn_validation(cdn, 'error')

    handler = HttpHandler(applications=applications, cdn=cdn,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins, check_origin=check_origin)

    def view_func():
        context = FlaskHttpContext()
        return handler.handle_request(context)

    view_func.__name__ = 'webio_view'
    return view_func


def wsgi_app(applications, cdn=True,
             static_dir=None,
             allowed_origins=None, check_origin=None,
             session_expire_seconds=None,
             session_cleanup_interval=None,
             max_payload_size='200M'):
    """Get the Flask WSGI app for running PyWebIO applications.

    The arguments of ``wsgi_app()`` have the same meaning as for :func:`pywebio.platform.flask.start_server`
    """
    cdn = cdn_validation(cdn, 'warn')

    app = Flask(__name__) if static_dir is None else Flask(__name__, static_url_path="/static",
                                                           static_folder=static_dir)
    page.MAX_PAYLOAD_SIZE = app.config['MAX_CONTENT_LENGTH'] = parse_file_size(max_payload_size)

    app.add_url_rule('/', 'webio_view', webio_view(
        applications=applications, cdn=cdn,
        session_expire_seconds=session_expire_seconds,
        session_cleanup_interval=session_cleanup_interval,
        allowed_origins=allowed_origins,
        check_origin=check_origin
    ), methods=['GET', 'POST', 'OPTIONS'])

    app.add_url_rule('/<path:p>', 'pywebio_static', lambda p: send_from_directory(STATIC_PATH, p))

    return app


def start_server(applications, port=8080, host='', cdn=True,
                 static_dir=None, remote_access=False,
                 allowed_origins=None, check_origin=None,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 debug=False,
                 max_payload_size='200M',
                 **flask_options):
    """Start a Flask server to provide the PyWebIO application as a web service.

    :param int session_expire_seconds: Session expiration time, in seconds(default 600s).
       If no client message is received within ``session_expire_seconds``, the session will be considered expired.
    :param int session_cleanup_interval: Session cleanup interval, in seconds(default 300s).
       The server will periodically clean up expired sessions and release the resources occupied by the sessions.
    :param bool debug: Flask debug mode.
       If enabled, the server will automatically reload for code changes.
    :param int/str max_payload_size: Max size of a request body which Flask can accept.
    :param flask_options: Additional keyword arguments passed to the ``flask.Flask.run``.
       For details, please refer: https://flask.palletsprojects.com/en/1.1.x/api/#flask.Flask.run

    The arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`
    """
    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    app = wsgi_app(applications, cdn=cdn, static_dir=static_dir, allowed_origins=allowed_origins,
                   check_origin=check_origin, session_expire_seconds=session_expire_seconds,
                   session_cleanup_interval=session_cleanup_interval, max_payload_size=max_payload_size)

    debug = Session.debug = os.environ.get('PYWEBIO_DEBUG', debug)
    if not debug:
        logging.getLogger('werkzeug').setLevel(logging.WARNING)

    running_from_reloader = werkzeug.serving.is_running_from_reloader()
    if remote_access and not running_from_reloader:
        start_remote_access_service(local_port=port)

    has_coro_target = any(iscoroutinefunction(target) or isgeneratorfunction(target) for
                          target in make_applications(applications).values())
    if has_coro_target and not running_from_reloader:
        threading.Thread(target=run_event_loop, daemon=True).start()

    app.run(host=host, port=port, debug=debug, threaded=True, use_evalex=False, **flask_options)
