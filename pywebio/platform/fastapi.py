import os
import asyncio
import json
import logging
from functools import partial

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.websockets import WebSocket
from starlette.websockets import WebSocketDisconnect

from .remote_access import start_remote_access_service
from .tornado import open_webbrowser_on_server_started
from .page import make_applications, render_page
from .utils import cdn_validation, OriginChecker, deserialize_binary_event, print_listen_address
from ..session import CoroutineBasedSession, ThreadBasedSession, register_session_implement_for_target, Session
from ..session.base import get_session_info_from_headers
from ..utils import get_free_port, STATIC_PATH, iscoroutinefunction, isgeneratorfunction, strip_space

logger = logging.getLogger(__name__)


def _webio_routes(applications, cdn, check_origin_func):
    """
    :param dict applications: dict of `name -> task function`
    :param bool/str cdn: Whether to load front-end static resources from CDN
    :param callable check_origin_func: check_origin_func(origin, host) -> bool
    """

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
        await websocket.accept()

        close_from_session_tag = False  # session close causes websocket close

        def send_msg_to_client(session: Session):
            for msg in session.get_task_commands():
                ioloop.create_task(websocket.send_json(msg))

        def close_from_session():
            nonlocal close_from_session_tag
            close_from_session_tag = True
            ioloop.create_task(websocket.close())
            logger.debug("WebSocket closed from session")

        session_info = get_session_info_from_headers(websocket.headers)
        session_info['user_ip'] = websocket.client.host or ''
        session_info['request'] = websocket
        session_info['backend'] = 'starlette'
        session_info['protocol'] = 'websocket'

        app_name = websocket.query_params.get('app', 'index')
        application = applications.get(app_name) or applications['index']

        if iscoroutinefunction(application) or isgeneratorfunction(application):
            session = CoroutineBasedSession(application, session_info=session_info,
                                            on_task_command=send_msg_to_client,
                                            on_session_close=close_from_session)
        else:
            session = ThreadBasedSession(application, session_info=session_info,
                                         on_task_command=send_msg_to_client,
                                         on_session_close=close_from_session, loop=ioloop)

        while True:
            try:
                msg = await websocket.receive()
                if msg["type"] == "websocket.disconnect":
                    raise WebSocketDisconnect(msg["code"])
                text, binary = msg.get('text'), msg.get('bytes')
                event = None
                if text:
                    event = json.loads(text)
                elif binary:
                    event = deserialize_binary_event(binary)
            except WebSocketDisconnect:
                if not close_from_session_tag:
                    # close session because client disconnected to server
                    session.close(nonblock=True)
                    logger.debug("WebSocket closed from client")
                break

            if event is not None:
                session.send_client_event(event)

    return [
        Route("/", http_endpoint),
        WebSocketRoute("/", websocket_endpoint)
    ]


def webio_routes(applications, cdn=True, allowed_origins=None, check_origin=None):
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

    return _webio_routes(applications=applications, cdn=cdn, check_origin_func=check_origin_func)


def start_server(applications, port=0, host='', cdn=True,
                 static_dir=None, remote_access=False, debug=False,
                 allowed_origins=None, check_origin=None,
                 auto_open_webbrowser=False,
                 **uvicorn_settings):
    """Start a FastAPI/Starlette server using uvicorn to provide the PyWebIO application as a web service.

    :param bool debug: Boolean indicating if debug tracebacks should be returned on errors.
    :param uvicorn_settings: Additional keyword arguments passed to ``uvicorn.run()``.
       For details, please refer: https://www.uvicorn.org/settings/

    The rest arguments of ``start_server()`` have the same meaning as for :func:`pywebio.platform.tornado.start_server`

    .. versionadded:: 1.3
    """

    app = asgi_app(applications, cdn=cdn, static_dir=static_dir, debug=debug,
                   allowed_origins=allowed_origins, check_origin=check_origin)

    if auto_open_webbrowser:
        asyncio.get_event_loop().create_task(open_webbrowser_on_server_started('localhost', port))

    if not host:
        host = '0.0.0.0'

    if port == 0:
        port = get_free_port()

    print_listen_address(host, port)

    if remote_access:
        start_remote_access_service(local_port=port)

    uvicorn.run(app, host=host, port=port, **uvicorn_settings)


def asgi_app(applications, cdn=True, static_dir=None, debug=False, allowed_origins=None, check_origin=None):
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
    routes = webio_routes(applications, cdn=cdn, allowed_origins=allowed_origins, check_origin=check_origin)
    if static_dir:
        routes.append(Mount('/static', app=StaticFiles(directory=static_dir), name="static"))
    routes.append(Mount('/pywebio_static', app=StaticFiles(directory=STATIC_PATH), name="pywebio_static"))
    return Starlette(routes=routes, debug=debug)
