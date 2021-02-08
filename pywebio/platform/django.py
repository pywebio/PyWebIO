import json
import logging
import threading
import os

from django.http import HttpResponse, HttpRequest

from .httpbased import HttpContext, HttpHandler, run_event_loop
from .utils import make_applications, cdn_validation
from ..utils import STATIC_PATH, iscoroutinefunction, isgeneratorfunction, get_free_port

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

    def request_json(self):
        """返回当前请求的json反序列化后的内容，若请求数据不为json格式，返回None"""
        try:
            return json.loads(self.request.body.decode('utf8'))
        except Exception:
            return None

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
    """获取在django中运行PyWebIO任务的视图函数。
    基于http请求与前端进行通讯

    :param list/dict/callable applications: PyWebIO应用。
    :param bool/str cdn: 是否从CDN加载前端静态资源，默认为 ``True`` 。设置成 ``False`` 时会从PyWebIO应用部署URL的同级目录下加载静态资源。
       支持传入自定义的URL来指定静态资源的部署地址
    :param int session_expire_seconds: 会话不活跃过期时间。
    :param int session_cleanup_interval: 会话清理间隔。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
    :param callable check_origin: 请求来源检查函数。

    关于各参数的详细说明见 :func:`pywebio.platform.django.start_server` 的同名参数。

    :return: Django视图函数
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


def start_server(applications, port=8080, host='localhost', cdn=True,
                 allowed_origins=None, check_origin=None,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 debug=False, **django_options):
    """启动一个 Django server 将PyWebIO应用作为Web服务提供。

    :param list/dict/callable applications: PyWebIO应用. 格式同 :func:`pywebio.platform.tornado.start_server` 的 ``applications`` 参数
    :param int port: 服务监听的端口。设置为 ``0`` 时，表示自动选择可用端口。
    :param str host: 服务绑定的地址。 ``host`` 可以是IP地址或者为hostname。如果为hostname，服务会监听所有与该hostname关联的IP地址。
        通过设置 ``host`` 为空字符串或 ``None`` 来将服务绑定到所有可用的地址上。
    :param bool/str cdn: 是否从CDN加载前端静态资源，默认为 ``True`` 。支持传入自定义的URL来指定静态资源的部署地址
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。格式同 :func:`pywebio.platform.tornado.start_server` 的 ``allowed_origins`` 参数
    :param callable check_origin: 请求来源检查函数。格式同 :func:`pywebio.platform.tornado.start_server` 的 ``check_origin`` 参数
    :param int session_expire_seconds: 会话过期时间。若 session_expire_seconds 秒内没有收到客户端的请求，则认为会话过期。
    :param int session_cleanup_interval: 会话清理间隔(秒)。服务端会周期性清理过期的会话，释放会话占用的资源。
    :param bool debug: 开启 Django debug mode 和一般访问日志的记录
    :param django_options: django应用的其他设置，见 https://docs.djangoproject.com/en/3.0/ref/settings/ .
        其中 ``DEBUG`` 、 ``ALLOWED_HOSTS`` 、 ``ROOT_URLCONF`` 、 ``SECRET_KEY`` 被PyWebIO设置，无法在 ``django_options`` 中指定
    """
    global urlpatterns

    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.urls import path
    from django.utils.crypto import get_random_string
    from django.views.static import serve

    if port == 0:
        port = get_free_port()

    if not host:
        host = '0.0.0.0'

    cdn = cdn_validation(cdn, 'warn')

    django_options.update(dict(
        DEBUG=debug,
        ALLOWED_HOSTS=["*"],  # Disable host header validation
        ROOT_URLCONF=__name__,  # Make this module the urlconf
        SECRET_KEY=get_random_string(10),  # We aren't using any security features but Django requires this setting
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

    use_tornado_wsgi = os.environ.get('PYWEBIO_DJANGO_WITH_TORNADO', True)
    if use_tornado_wsgi:
        app = get_wsgi_application()  # load app

        import tornado.wsgi
        container = tornado.wsgi.WSGIContainer(app)
        http_server = tornado.httpserver.HTTPServer(container)
        http_server.listen(port, address=host)
        tornado.ioloop.IOLoop.current().start()
    else:
        from django.core.management import call_command
        has_coro_target = any(iscoroutinefunction(target) or isgeneratorfunction(target) for
                              target in make_applications(applications).values())
        if has_coro_target:
            threading.Thread(target=run_event_loop, daemon=True).start()

        call_command('runserver', '%s:%d' % (host, port))
