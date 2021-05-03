import asyncio
import fnmatch
import json
import logging
from functools import partial
from os import path, listdir
from urllib.parse import urlparse

from aiohttp import web

from .remote_access import start_remote_access_service
from .tornado import open_webbrowser_on_server_started
from .utils import make_applications, render_page, cdn_validation, deserialize_binary_event
from ..session import CoroutineBasedSession, ThreadBasedSession, register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, STATIC_PATH, iscoroutinefunction, isgeneratorfunction

logger = logging.getLogger(__name__)


def _check_origin(origin, allowed_origins, host):
    if _is_same_site(origin, host):
        return True

    return any(
        fnmatch.fnmatch(origin, patten)
        for patten in allowed_origins
    )


def _is_same_site(origin, host):
    """判断 origin 和 host 是否一致。origin 和 host 都为http协议请求头"""
    parsed_origin = urlparse(origin)
    origin = parsed_origin.netloc
    origin = origin.lower()

    # Check to see that origin matches host directly, including ports
    return origin == host


def _webio_handler(applications, cdn, websocket_settings, check_origin_func=_is_same_site):
    """
    :param dict applications: dict of `name -> task function`
    :param bool/str cdn: Whether to load front-end static resources from CDN
    :param callable check_origin_func: check_origin_func(origin, host) -> bool
    :return: aiohttp Request Handler
    """
    ioloop = asyncio.get_event_loop()

    async def wshandle(request: web.Request):
        origin = request.headers.get('origin')
        if origin and not check_origin_func(origin=origin, host=request.host):
            return web.Response(status=403, text="Cross origin websockets not allowed")

        if request.headers.get("Upgrade", "").lower() != "websocket":
            # Backward compatible
            if request.query.getone('test', ''):
                return web.Response(text="")

            app_name = request.query.getone('app', 'index')
            app = applications.get(app_name) or applications['index']
            html = render_page(app, protocol='ws', cdn=cdn)
            return web.Response(body=html, content_type='text/html')

        ws = web.WebSocketResponse(**websocket_settings)
        await ws.prepare(request)

        close_from_session_tag = False  # 是否由session主动关闭连接

        def send_msg_to_client(session: Session):
            for msg in session.get_task_commands():
                msg_str = json.dumps(msg)
                ioloop.create_task(ws.send_str(msg_str))

        def close_from_session():
            nonlocal close_from_session_tag
            close_from_session_tag = True
            ioloop.create_task(ws.close())
            logger.debug("WebSocket closed from session")

        session_info = get_session_info_from_headers(request.headers)
        session_info['user_ip'] = request.remote
        session_info['request'] = request
        session_info['backend'] = 'aiohttp'
        session_info['protocol'] = 'websocket'

        app_name = request.query.getone('app', 'index')
        application = applications.get(app_name) or applications['index']

        if iscoroutinefunction(application) or isgeneratorfunction(application):
            session = CoroutineBasedSession(application, session_info=session_info,
                                            on_task_command=send_msg_to_client,
                                            on_session_close=close_from_session)
        else:
            session = ThreadBasedSession(application, session_info=session_info,
                                         on_task_command=send_msg_to_client,
                                         on_session_close=close_from_session, loop=ioloop)

        # see: https://github.com/aio-libs/aiohttp/issues/1768
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.text:
                    data = msg.json()
                elif msg.type == web.WSMsgType.binary:
                    data = deserialize_binary_event(msg.data)
                elif msg.type == web.WSMsgType.close:
                    raise asyncio.CancelledError()

                if data is not None:
                    session.send_client_event(data)
        finally:
            if not close_from_session_tag:
                # close session because client disconnected to server
                session.close(nonblock=True)
                logger.debug("WebSocket closed from client")

        return ws

    return wshandle


def webio_handler(applications, cdn=True, allowed_origins=None, check_origin=None, websocket_settings=None):
    """Get the `Request Handler <https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler>`_ coroutine for running PyWebIO applications in aiohttp.
    The handler communicates with the browser by WebSocket protocol.

    The arguments of ``webio_handler()`` have the same meaning as for :func:`pywebio.platform.aiohttp.start_server`

    :return: aiohttp Request Handler
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    websocket_settings = websocket_settings or {}

    cdn = cdn_validation(cdn, 'error')

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, host: _is_same_site(origin, host) or check_origin(origin)

    return _webio_handler(applications=applications, cdn=cdn,
                          check_origin_func=check_origin_func,
                          websocket_settings=websocket_settings)


def static_routes(prefix='/'):
    """获取用于提供PyWebIO静态文件的aiohttp路由列表
    Get the aiohttp routes list for PyWebIO static files hosting.

    :param str prefix: The URL path of static file hosting, the default is the root path ``/``
    :return: aiohttp routes list
    """

    async def index(request):
        return web.FileResponse(path.join(STATIC_PATH, 'index.html'))

    files = [path.join(STATIC_PATH, d) for d in listdir(STATIC_PATH)]
    dirs = filter(path.isdir, files)
    routes = [web.static(prefix + path.basename(d), d) for d in dirs]
    routes.append(web.get(prefix, index))
    return routes


def start_server(applications, port=0, host='', debug=False,
                 cdn=True, static_dir=None, remote_access=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
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

    handler = webio_handler(applications, cdn=cdn, allowed_origins=allowed_origins,
                            check_origin=check_origin, websocket_settings=websocket_settings)

    app = web.Application(**aiohttp_settings)
    app.router.add_routes([web.get('/', handler)])
    if static_dir is not None:
        app.router.add_routes([web.static('/static', static_dir)])
    app.router.add_routes(static_routes())

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('localhost', port))

    if debug:
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    print('Listen on %s:%s' % (host, port))

    if remote_access or remote_access == {}:
        if remote_access is True: remote_access = {}
        start_remote_access_service(**remote_access, local_port=port)

    web.run_app(app, host=host, port=port)
