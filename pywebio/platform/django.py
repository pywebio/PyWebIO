import json
import logging
import os
import threading

from django.http import HttpResponse, HttpRequest

from . import utils
from .httpbased import HttpContext, HttpHandler, run_event_loop
from .remote_access import start_remote_access_service
from .utils import make_applications, cdn_validation
from ..utils import STATIC_PATH, iscoroutinefunction, isgeneratorfunction, get_free_port, parse_file_size

logger = logging.getLogger(__name__)


class DjangoHttpContext(HttpContext):
    backend_name = 'django'

    def __init__(self, request: HttpRequest):
        self.request = request
        self.response = HttpResponse()

    def request_obj(self):
        """返回当前请求对象"""
        return self.request

    def request_method(self):
        """返回当前请求的方法，大写"""
        return self.request.method

    def request_headers(self):
        """返回当前请求的header字典"""
        return self.request.headers

    def request_url_parameter(self, name, default=None):
        """返回当前请求的URL参数"""
        return self.request.GET.get(name, default=default)

    def request_body(self):
        return self.request.body

    def set_header(self, name, value):
        """为当前响应设置header"""
        self.response[name] = value

    def set_status(self, status: int):
        """为当前响应设置http status"""
        self.response.status_code = status

    def set_content(self, content, json_type=False):
        """设置相应的内容

        :param content:
        :param bool json_type: content是否要序列化成json格式，并将 content-type 设置为application/json
        """
        # self.response.content accept str and byte
        if json_type:
            self.set_header('content-type', 'application/json')
            self.response.content = json.dumps(content)
        else:
            self.response.content = content

    def get_response(self):
        """获取当前的响应对象，用于在私图函数中返回"""
        return self.response

    def get_client_ip(self):
        """获取用户的ip"""
        return self.request.META.get('REMOTE_ADDR')


def webio_view(applications, cdn=True,
               session_expire_seconds=None,
               session_cleanup_interval=None,
               allowed_origins=None, check_origin=None):
    """Get the view function for running PyWebIO applications in Django.
    The view communicates with the browser by HTTP protocol.

    The arguments of ``webio_view()`` have the same meaning as for :func:`pywebio.platform.flask.webio_view`
    """
    cdn = cdn_validation(cdn, 'error')
    handler = HttpHandler(applications=applications, cdn=cdn,
                          session_expire_seconds=session_expire_seconds,
                          session_cleanup_interval=session_cleanup_interval,
                          allowed_origins=allowed_origins, check_origin=check_origin)

    from django.views.decorators.csrf import csrf_exempt

    @csrf_exempt
    def view_func(request):
        context = DjangoHttpContext(request)
        return handler.handle_request(context)

    view_func.__name__ = 'webio_view'
    return view_func


urlpatterns = []


def wsgi_app(applications, cdn=True,
                 static_dir=None,
                 allowed_origins=None, check_origin=None,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 debug=False, max_payload_size='200M', **django_options):
    """Get the Django WSGI app for running PyWebIO applications.

    The arguments of ``wsgi_app()`` have the same meaning as for :func:`pywebio.platform.django.start_server`
    """
    global urlpatterns

    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.urls import path
    from django.utils.crypto import get_random_string
    from django.views.static import serve

    cdn = cdn_validation(cdn, 'warn')

    max_payload_size = parse_file_size(max_payload_size)
    utils.MAX_PAYLOAD_SIZE = max_payload_size

    django_options.update(dict(
        DEBUG=debug,
        ALLOWED_HOSTS=["*"],  # Disable host header validation
        ROOT_URLCONF=__name__,  # Make this module the urlconf
        SECRET_KEY=get_random_string(10),  # We aren't using any security features but Django requires this setting
        DATA_UPLOAD_MAX_MEMORY_SIZE=max_payload_size
    ))
    django_options.setdefault('LOGGING', {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(asctime)s] %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'loggers': {
            'django.server': {
                'level': 'INFO' if debug else 'WARN',
                'handlers': ['console'],
            },
        },
    })
    settings.configure(**django_options)

    webio_view_func = webio_view(
        applications=applications, cdn=cdn,
        session_expire_seconds=session_expire_seconds,
        session_cleanup_interval=session_cleanup_interval,
        allowed_origins=allowed_origins,
        check_origin=check_origin
    )

    urlpatterns = [
        path(r"", webio_view_func),
        path(r'<path:path>', serve, {'document_root': STATIC_PATH}),
    ]
    if static_dir is not None:
        urlpatterns.insert(0, path(r'static/<path:path>', serve, {'document_root': static_dir}))

    return get_wsgi_application()


def start_server(applications, port=8080, host='', cdn=True,
                 static_dir=None, remote_access=False,
                 allowed_origins=None, check_origin=None,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 debug=False, max_payload_size='200M', **django_options):
    """Start a Django server to provide the PyWebIO application as a web service.

    :param bool debug: Django debug mode.
       See `Django doc <https://docs.djangoproject.com/en/3.0/ref/settings/#debug>`_ for more detail.
    :param django_options: Additional settings to django server.
       For details, please refer: https://docs.djangoproject.com/en/3.0/ref/settings/ .
       Among them, ``DEBUG``, ``ALLOWED_HOSTS``, ``ROOT_URLCONF``, ``SECRET_KEY`` are set by PyWebIO and cannot be specified in ``django_options``.

    The rest arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.flask.start_server`
    """
    if port == 0:
        port = get_free_port()

    if not host:
        host = '0.0.0.0'

    max_payload_size = parse_file_size(max_payload_size)
    app = wsgi_app(applications, cdn=cdn, static_dir=static_dir, allowed_origins=allowed_origins,
                   check_origin=check_origin, session_expire_seconds=session_expire_seconds,
                   session_cleanup_interval=session_cleanup_interval,
                   debug=debug, max_payload_size=max_payload_size, **django_options)

    if remote_access or remote_access == {}:
        if remote_access is True: remote_access = {}
        start_remote_access_service(**remote_access, local_port=port)

    use_tornado_wsgi = os.environ.get('PYWEBIO_DJANGO_WITH_TORNADO', True)
    if use_tornado_wsgi:
        import tornado.wsgi
        container = tornado.wsgi.WSGIContainer(app)
        http_server = tornado.httpserver.HTTPServer(container, max_buffer_size=max_payload_size)
        http_server.listen(port, address=host)
        tornado.ioloop.IOLoop.current().start()
    else:
        from django.core.management import call_command
        has_coro_target = any(iscoroutinefunction(target) or isgeneratorfunction(target) for
                              target in make_applications(applications).values())
        if has_coro_target:
            threading.Thread(target=run_event_loop, daemon=True).start()

        call_command('runserver', '%s:%d' % (host, port))
