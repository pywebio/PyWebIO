import asyncio
import fnmatch
import json
import logging
from functools import partial
from os import path, listdir
from urllib.parse import urlparse

from aiohttp import web

from .tornado import open_webbrowser_on_server_started
from ..session import CoroutineBasedSession, ThreadBasedSession, register_session_implement_for_target, AbstractSession
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, STATIC_PATH

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


def _webio_handler(target, session_cls, websocket_settings, check_origin_func=_is_same_site):
    """获取用于Tornado进行整合的RequestHandle类

    :param target: 任务函数
    :param session_cls: 会话实现类
    :param callable check_origin_func: check_origin_func(origin, handler) -> bool
    :return: Tornado RequestHandle类
    """
    ioloop = asyncio.get_event_loop()

    async def wshandle(request: web.Request):
        origin = request.headers.get('origin')
        if origin and not check_origin_func(origin=origin, host=request.host):
            return web.Response(status=403, text="Cross origin websockets not allowed")

        ws = web.WebSocketResponse(**websocket_settings)
        await ws.prepare(request)

        close_from_session_tag = False  # 是否由session主动关闭连接

        def send_msg_to_client(session: AbstractSession):
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
        if session_cls is CoroutineBasedSession:
            session = CoroutineBasedSession(target, session_info=session_info,
                                            on_task_command=send_msg_to_client,
                                            on_session_close=close_from_session)
        elif session_cls is ThreadBasedSession:
            session = ThreadBasedSession(target, session_info=session_info,
                                         on_task_command=send_msg_to_client,
                                         on_session_close=close_from_session, loop=ioloop)
        else:
            raise RuntimeError("Don't support session type:%s" % session_cls)

        async for msg in ws:
            if msg.type == web.WSMsgType.text:
                data = msg.json()
                if data is not None:
                    session.send_client_event(data)
            elif msg.type == web.WSMsgType.binary:
                pass
            elif msg.type == web.WSMsgType.close:
                if not close_from_session_tag:
                    session.close()
                    logger.debug("WebSocket closed from client")

        return ws

    return wshandle


def webio_handler(target, allowed_origins=None, check_origin=None, websocket_settings=None):
    """获取在aiohttp中运行PyWebIO任务函数的 `Request Handle <https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler>`_ 协程。
    Request Handle基于WebSocket协议与浏览器进行通讯。

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com`` 、
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param dict websocket_settings: 创建 aiohttp WebSocketResponse 时使用的参数。见 https://docs.aiohttp.org/en/stable/web_reference.html#websocketresponse
    :return: aiohttp Request Handler
    """
    session_cls = register_session_implement_for_target(target)

    websocket_settings = websocket_settings or {}

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(target=target, session_cls=session_cls, check_origin_func=check_origin_func,
                          websocket_settings=websocket_settings)


def static_routes(static_path):
    """获取用于提供PyWebIO静态文件的aiohttp路由"""

    async def index(request):
        return web.FileResponse(path.join(STATIC_PATH, 'index.html'))

    files = [path.join(static_path, d) for d in listdir(static_path)]
    dirs = filter(path.isdir, files)
    routes = [web.static('/' + path.basename(d), d) for d in dirs]
    routes.append(web.get('/', index))
    return routes


def start_server(target, port=0, host='', debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 websocket_settings=None,
                 **aiohttp_settings):
    """启动一个 aiohttp server 将 ``target`` 任务函数作为Web服务提供。

    :param target: 任务函数。任务函数为协程函数时，使用 :ref:`基于协程的会话实现 <coroutine_based_session>` ；任务函数为普通函数时，使用基于线程的会话实现。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
    :param int port: server bind port. set ``0`` to find a free port number to use
    :param str host: server bind host. ``host`` may be either an IP address or hostname.  If it's a hostname,
        the server will listen on all IP addresses associated with the name.
        set empty string or to listen on all available interfaces.
    :param bool debug: asyncio Debug Mode
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议和域名和端口部分，允许使用 Unix shell 风格的匹配模式:

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq内的字符
        - ``[!seq]`` 匹配不在seq内的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议和域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param bool auto_open_webbrowser: Whether or not auto open web browser when server is started (if the operating system allows it) .
    :param dict websocket_settings: 创建 aiohttp WebSocketResponse 时使用的参数。见 https://docs.aiohttp.org/en/stable/web_reference.html#websocketresponse
    :param aiohttp_settings: 需要传给 aiohttp Application 的参数。可用参数见 https://docs.aiohttp.org/en/stable/web_reference.html#application
    """
    kwargs = locals()

    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    handler = webio_handler(target, allowed_origins=allowed_origins, check_origin=check_origin,
                            websocket_settings=websocket_settings)

    app = web.Application(**aiohttp_settings)
    app.add_routes([web.get('/io', handler)])
    app.add_routes(static_routes(STATIC_PATH))

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('localhost', port))

    if debug:
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    print('Listen on %s:%s' % (host, port))
    web.run_app(app, host=host, port=port)
