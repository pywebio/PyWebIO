import asyncio
import logging
import os
import typing
from functools import partial

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.websockets import WebSocket, WebSocketState
from starlette.websockets import WebSocketDisconnect

from . import page
from .page import make_applications, render_page
from .remote_access import start_remote_access_service
from .tornado import open_webbrowser_on_server_started
from .utils import cdn_validation, OriginChecker, print_listen_address
from ..session import register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, STATIC_PATH, strip_space, parse_file_size

logger = logging.getLogger(__name__)
from .adaptor import ws as ws_adaptor


class WebSocketConnection(ws_adaptor.WebSocketConnection):

    def __init__(self, websocket: WebSocket, ioloop):
        self.ws = websocket
        self.ioloop = ioloop

    def get_query_argument(self, name) -> typing.Optional[str]:
        return self.ws.query_params.get(name, None)

    def make_session_info(self) -> dict:
        session_info = get_session_info_from_headers(self.ws.headers)
        session_info['user_ip'] = self.ws.client.host or ''
        session_info['request'] = self.ws
        session_info['backend'] = 'starlette'
        session_info['protocol'] = 'websocket'
        return session_info

    def write_message(self, message: dict):
        self.ioloop.create_task(self.ws.send_json(message))

    def closed(self) -> bool:
        return self.ws.application_state == WebSocketState.DISCONNECTED

    def close(self):
        self.ioloop.create_task(self.ws.close())


def _webio_routes(applications, cdn, check_origin_func, reconnect_timeout):
    """
    :param dict applications: dict of `name -> task function`
    :param bool/str cdn: Whether to load front-end static resources from CDN
    :param callable check_origin_func: check_origin_func(origin, host) -> bool
    """

    ws_adaptor.set_expire_second(reconnect_timeout)

    async def http_endpoint(request: Request):
        origin = request.headers.get('origin')
        if origin and not check_origin_func(origin=origin, host=request.headers.get('host')):
            return HTMLResponse(status_code=403, content="Cross origin websockets not allowed")

        # Backward compatible
        if request.query_params.get('test'):
            return HTMLResponse(content="")

        app_name = request.query_params.get('app', 'index')
        app = applications.get(app_name) or applications['index']
        no_cdn = cdn is True and request.query_params.get('_pywebio_cdn', '') == 'false'
        html = render_page(app, protocol='ws', cdn=False if no_cdn else cdn)
        return HTMLResponse(content=html)

    async def websocket_endpoint(websocket: WebSocket):
        ioloop = asyncio.get_event_loop()
        asyncio.get_event_loop().create_task(ws_adaptor.session_clean_task())

        await websocket.accept()

        app_name = websocket.query_params.get('app', 'index')
        application = applications.get(app_name) or applications['index']

        conn = WebSocketConnection(websocket, ioloop)
        handler = ws_adaptor.WebSocketHandler(
            connection=conn, application=application, reconnectable=bool(reconnect_timeout), ioloop=ioloop
        )

        while True:
            try:
                msg = await websocket.receive()
                if msg["type"] == "websocket.disconnect":
                    raise WebSocketDisconnect(msg["code"])
                text, binary = msg.get('text'), msg.get('bytes')
                if text:
                    handler.send_client_data(text)
                if binary:
                    handler.send_client_data(binary)
            except WebSocketDisconnect:
                handler.notify_connection_lost()
                break

    return [
        Route("/", http_endpoint),
        WebSocketRoute("/", websocket_endpoint)
    ]


def webio_routes(applications, cdn=True, reconnect_timeout=0, allowed_origins=None, check_origin=None):
    """Get the FastAPI/Starlette routes for running PyWebIO applications.

    The API communicates with the browser using WebSocket protocol.

    The arguments of ``webio_routes()`` have the same meaning as for :func:`pywebio.platform.fastapi.start_server`

    .. versionadded:: 1.3

    :return: FastAPI/Starlette routes
    """
    try:
        import websockets
    except Exception:
        raise RuntimeError(strip_space("""
        Missing dependency package `websockets` for websocket support.
        You can install it with the following command:
            pip install websockets
        """.strip(), n=8)) from None

    applications = make_applications(applications)
    for target in applications.values():
        register_session_implement_for_target(target)

    cdn = cdn_validation(cdn, 'error')

    if check_origin is None:
        check_origin_func = partial(OriginChecker.check_origin, allowed_origins=allowed_origins or [])
    else:
        check_origin_func = lambda origin, host: OriginChecker.is_same_site(origin, host) or check_origin(origin)

    return _webio_routes(applications=applications, cdn=cdn, check_origin_func=check_origin_func,
                         reconnect_timeout=reconnect_timeout)


def start_server(applications, port=0, host='', cdn=True, reconnect_timeout=0,
                 static_dir=None, remote_access=False, debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 max_payload_size='200M',
                 **uvicorn_settings):
    """Start a FastAPI/Starlette server using uvicorn to provide the PyWebIO application as a web service.

    :param bool debug: Boolean indicating if debug tracebacks should be returned on errors.
    :param uvicorn_settings: Additional keyword arguments passed to ``uvicorn.run()``.
       For details, please refer: https://www.uvicorn.org/settings/

    The rest arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`

    .. versionadded:: 1.3
    """

    app = asgi_app(applications, cdn=cdn, reconnect_timeout=reconnect_timeout,
                   static_dir=static_dir, debug=debug,
                   allowed_origins=allowed_origins, check_origin=check_origin)

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('127.0.0.1', port))

    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    print_listen_address(host, port)

    if remote_access:
        start_remote_access_service(local_port=port)

    page.MAX_PAYLOAD_SIZE = max_payload_size = parse_file_size(max_payload_size)
    uvicorn_settings = uvicorn_settings or {}
    uvicorn_settings.setdefault('ws_max_size', max_payload_size)

    uvicorn.run(app, host=host, port=port, **uvicorn_settings)


def asgi_app(applications, cdn=True, reconnect_timeout=0, static_dir=None, debug=False, allowed_origins=None,
             check_origin=None):
    """Get the starlette/Fastapi ASGI app for running PyWebIO applications.

    Use :func:`pywebio.platform.fastapi.webio_routes` if you prefer handling static files yourself.

    The arguments of ``asgi_app()`` have the same meaning as for :func:`pywebio.platform.fastapi.start_server`

    :Example:

    To be used with ``FastAPI.mount()`` to include pywebio as a subapp into an existing Starlette/FastAPI application::

        from fastapi import FastAPI
        from pywebio.platform.fastapi import asgi_app
        from pywebio.output import put_text
        app = FastAPI()
        subapp = asgi_app(lambda: put_text("hello from pywebio"))
        app.mount("/pywebio", subapp)

    :Returns: Starlette/Fastapi ASGI app

    .. versionadded:: 1.3
    """
    try:
        from starlette.staticfiles import StaticFiles
    except Exception:
        raise RuntimeError(strip_space("""
        Missing dependency package `aiofiles` for static file serving.
        You can install it with the following command:
            pip install aiofiles
        """.strip(), n=8)) from None
    debug = Session.debug = os.environ.get('PYWEBIO_DEBUG', debug)
    cdn = cdn_validation(cdn, 'warn')
    if cdn is False:
        cdn = 'pywebio_static'
    routes = webio_routes(applications, cdn=cdn, reconnect_timeout=reconnect_timeout,
                          allowed_origins=allowed_origins, check_origin=check_origin)
    if static_dir:
        routes.append(Mount('/static', app=StaticFiles(directory=static_dir), name="static"))
    routes.append(Mount('/pywebio_static', app=StaticFiles(directory=STATIC_PATH), name="pywebio_static"))
    return Starlette(routes=routes, debug=debug)
