import asyncio
import fnmatch
import json
import logging
import os
import typing
from functools import partial
from urllib.parse import urlparse

from aiohttp import web

from . import page
from .adaptor import ws as ws_adaptor
from .page import make_applications, render_page
from .remote_access import start_remote_access_service
from .tornado import open_webbrowser_on_server_started
from .utils import cdn_validation, print_listen_address
from ..session import register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, STATIC_PATH, parse_file_size

logger = logging.getLogger(__name__)


def _check_origin(origin, allowed_origins, host):
    if _is_same_site(origin, host):
        return True

    return any(
        fnmatch.fnmatch(origin, pattern)
        for pattern in allowed_origins
    )


def _is_same_site(origin, host):
    """判断 origin 和 host 是否一致。origin 和 host 都为http协议请求头"""
    parsed_origin = urlparse(origin)
    origin = parsed_origin.netloc
    origin = origin.lower()

    # Check to see that origin matches host directly, including ports
    return origin == host


class WebSocketConnection(ws_adaptor.WebSocketConnection):

    def __init__(self, ws: web.WebSocketResponse, http: web.Request, ioloop):
        self.ws = ws
        self.http = http
        self.ioloop = ioloop

    def get_query_argument(self, name) -> typing.Optional[str]:
        return self.http.query.getone(name, None)

    def make_session_info(self) -> dict:
        session_info = get_session_info_from_headers(self.http.headers)
        session_info['user_ip'] = self.http.remote
        session_info['request'] = self.http
        session_info['backend'] = 'aiohttp'
        session_info['protocol'] = 'websocket'
        return session_info

    def write_message(self, message: dict):
        msg_str = json.dumps(message)
        self.ioloop.create_task(self.ws.send_str(msg_str))

    def closed(self) -> bool:
        return self.ws.closed

    def close(self):
        self.ioloop.create_task(self.ws.close())


def _webio_handler(applications, cdn, websocket_settings, reconnect_timeout=0, check_origin_func=_is_same_site):
    """
    :param dict applications: dict of `name -> task function`
    :param bool/str cdn: Whether to load front-end static resources from CDN
    :param callable check_origin_func: check_origin_func(origin, host) -> bool
    :return: aiohttp Request Handler
    """
    ws_adaptor.set_expire_second(reconnect_timeout)

    async def wshandle(request: web.Request):
        ioloop = asyncio.get_event_loop()
        asyncio.get_event_loop().create_task(ws_adaptor.session_clean_task())

        origin = request.headers.get('origin')
        if origin and not check_origin_func(origin=origin, host=request.host):
            return web.Response(status=403, text="Cross origin websockets not allowed")

        if request.headers.get("Upgrade", "").lower() != "websocket":
            # Backward compatible
            if request.query.getone('test', ''):
                return web.Response(text="")

            app_name = request.query.getone('app', 'index')
            app = applications.get(app_name) or applications['index']
            no_cdn = cdn is True and request.query.getone('_pywebio_cdn', '') == 'false'
            html = render_page(app, protocol='ws', cdn=False if no_cdn else cdn)
            return web.Response(body=html, content_type='text/html')

        ws = web.WebSocketResponse(**websocket_settings)
        await ws.prepare(request)

        app_name = request.query.getone('app', 'index')
        application = applications.get(app_name) or applications['index']

        conn = WebSocketConnection(ws, request, ioloop)
        handler = ws_adaptor.WebSocketHandler(
            connection=conn, application=application, reconnectable=bool(reconnect_timeout), ioloop=ioloop
        )

        # see: https://github.com/aio-libs/aiohttp/issues/1768
        try:
            async for msg in ws:
                if msg.type in (web.WSMsgType.text, web.WSMsgType.binary):
                    handler.send_client_data(msg.data)
                elif msg.type == web.WSMsgType.close:
                    raise asyncio.CancelledError()
        finally:
            handler.notify_connection_lost()

        return ws

    return wshandle


def webio_handler(applications, cdn=True, reconnect_timeout=0, allowed_origins=None, check_origin=None,
                  max_payload_size='200M', websocket_settings=None):
    """Get the `Request Handler <https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler>`_ coroutine for running PyWebIO applications in aiohttp.
    The handler communicates with the browser by WebSocket protocol.

    The arguments of ``webio_handler()`` have the same meaning as for :func:`pywebio.platform.aiohttp.start_server`

    :return: aiohttp Request Handler
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    websocket_settings = websocket_settings or {}

    page.MAX_PAYLOAD_SIZE = max_payload_size = parse_file_size(max_payload_size)
    websocket_settings.setdefault('max_msg_size', max_payload_size)

    cdn = cdn_validation(cdn, 'error')

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, host: _is_same_site(origin, host) or check_origin(origin)

    return _webio_handler(applications=applications, cdn=cdn,
                          check_origin_func=check_origin_func,
                          reconnect_timeout=reconnect_timeout,
                          websocket_settings=websocket_settings)


def static_routes(prefix='/'):
    """获取用于提供PyWebIO静态文件的aiohttp路由列表
    Get the aiohttp routes list for PyWebIO static files hosting.

    :param str prefix: The URL path of static file hosting, the default is the root path ``/``
    :return: aiohttp routes list
    """
    files = [os.path.join(STATIC_PATH, d) for d in os.listdir(STATIC_PATH)]
    dirs = filter(os.path.isdir, files)
    routes = [web.static(prefix + os.path.basename(d), d) for d in dirs]
    return routes


def start_server(applications, port=0, host='', debug=False,
                 cdn=True, static_dir=None, remote_access=False,
                 reconnect_timeout=0,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 max_payload_size='200M',
                 websocket_settings=None,
                 **aiohttp_settings):
    """Start a aiohttp server to provide the PyWebIO application as a web service.


    :param dict websocket_settings: The  parameters passed to the constructor of ``aiohttp.web.WebSocketResponse``.
       For details, please refer: https://docs.aiohttp.org/en/stable/web_reference.html#websocketresponse
    :param aiohttp_settings: Additional keyword arguments passed to the constructor of ``aiohttp.web.Application``.
       For details, please refer: https://docs.aiohttp.org/en/stable/web_reference.html#application

    The rest arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`
    """
    kwargs = locals()

    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    cdn = cdn_validation(cdn, 'warn')

    handler = webio_handler(applications, cdn=cdn, allowed_origins=allowed_origins, reconnect_timeout=reconnect_timeout,
                            check_origin=check_origin, max_payload_size=max_payload_size,
                            websocket_settings=websocket_settings)

    app = web.Application(**aiohttp_settings)
    app.router.add_routes([web.get('/', handler)])
    if static_dir is not None:
        app.router.add_routes([web.static('/static', static_dir)])
    app.router.add_routes(static_routes())

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('127.0.0.1', port))

    debug = Session.debug = os.environ.get('PYWEBIO_DEBUG', debug)
    if debug:
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    print_listen_address(host, port)

    if remote_access:
        start_remote_access_service(local_port=port)

    web.run_app(app, host=host, port=port)
