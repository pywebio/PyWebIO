import asyncio
import fnmatch
import json
import logging
from functools import partial
from os import path, listdir
from urllib.parse import urlparse

from aiohttp import web

from .tornado import open_webbrowser_on_server_started
from .utils import make_applications
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


def _webio_handler(applications, websocket_settings, check_origin_func=_is_same_site):
    """获取用于Tornado进行整合的RequestHandle类

    :param dict applications: 任务名->任务函数 的映射
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


def webio_handler(applications, allowed_origins=None, check_origin=None, websocket_settings=None):
    """获取在aiohttp中运行PyWebIO任务函数的 `Request Handle <https://docs.aiohttp.org/en/stable/web_quickstart.html#aiohttp-web-handler>`_ 协程。
    Request Handle基于WebSocket协议与浏览器进行通讯。

    :param list/dict/callable applications: PyWebIO应用。
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
    :param callable check_origin: 请求来源检查函数。
    :param dict websocket_settings: 创建 aiohttp WebSocketResponse 时使用的参数。见 https://docs.aiohttp.org/en/stable/web_reference.html#websocketresponse

    关于 ``applications`` 、 ``allowed_origins`` 、 ``check_origin`` 参数的详细说明见 :func:`pywebio.platform.aiohttp.start_server` 的同名参数。

    :return: aiohttp Request Handler
    """
    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    websocket_settings = websocket_settings or {}

    if check_origin is None:
        check_origin_func = partial(_check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, handler: _is_same_site(origin, handler) or check_origin(origin)

    return _webio_handler(applications=applications,
                          check_origin_func=check_origin_func,
                          websocket_settings=websocket_settings)


def static_routes(prefix='/'):
    """获取用于提供PyWebIO静态文件的aiohttp路由列表

    :param str prefix: 静态文件托管的URL路径，默认为根路径 ``/``
    :return: aiohttp路由列表
    """

    async def index(request):
        return web.FileResponse(path.join(STATIC_PATH, 'index.html'))

    files = [path.join(STATIC_PATH, d) for d in listdir(STATIC_PATH)]
    dirs = filter(path.isdir, files)
    routes = [web.static(prefix + path.basename(d), d) for d in dirs]
    routes.append(web.get(prefix, index))
    return routes


def start_server(applications, port=0, host='', debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 websocket_settings=None,
                 **aiohttp_settings):
    """启动一个 aiohttp server 将PyWebIO应用作为Web服务提供。

    :param list/dict/callable applications: PyWebIO应用. 格式同 :func:`pywebio.platform.tornado.start_server` 的 ``applications`` 参数
    :param int port: 服务监听的端口。设置为 ``0`` 时，表示自动选择可用端口。
    :param str host: 服务绑定的地址。 ``host`` 可以是IP地址或者为hostname。如果为hostname，服务会监听所有与该hostname关联的IP地址。
        通过设置 ``host`` 为空字符串或 ``None`` 来将服务绑定到所有可用的地址上。
    :param bool debug: 是否开启asyncio的Debug模式
    :param list allowed_origins: 除当前域名外，服务器还允许的请求的来源列表。
        来源包含协议、域名和端口部分，允许使用 Unix shell 风格的匹配模式(全部规则参见 `Python文档 <https://docs.python.org/zh-tw/3/library/fnmatch.html>`_ ):

        - ``*`` 为通配符
        - ``?`` 匹配单个字符
        - ``[seq]`` 匹配seq中的字符
        - ``[!seq]`` 匹配不在seq中的字符

        比如 ``https://*.example.com`` 、 ``*://*.example.com``
    :param callable check_origin: 请求来源检查函数。接收请求来源(包含协议、域名和端口部分)字符串，
        返回 ``True/False`` 。若设置了 ``check_origin`` ， ``allowed_origins`` 参数将被忽略
    :param bool auto_open_webbrowser: 当服务启动后，是否自动打开浏览器来访问服务。（该操作需要操作系统支持）
    :param dict websocket_settings: 创建 aiohttp WebSocketResponse 时使用的参数。见 https://docs.aiohttp.org/en/stable/web_reference.html#websocketresponse
    :param aiohttp_settings: 需要传给 aiohttp Application 的参数。可用参数见 https://docs.aiohttp.org/en/stable/web_reference.html#application
    """
    kwargs = locals()

    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    handler = webio_handler(applications, allowed_origins=allowed_origins, check_origin=check_origin,
                            websocket_settings=websocket_settings)

    app = web.Application(**aiohttp_settings)
    app.router.add_routes([web.get('/io', handler)])
    app.router.add_routes(static_routes())

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('localhost', port))

    if debug:
        logging.getLogger("asyncio").setLevel(logging.DEBUG)

    print('Listen on %s:%s' % (host, port))
    web.run_app(app, host=host, port=port)
