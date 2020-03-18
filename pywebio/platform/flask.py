"""
Flask backend

"""
import asyncio
import threading
import time
from functools import partial
from typing import Dict

from flask import Flask, request, jsonify, send_from_directory

from . import STATIC_PATH
from ..framework import WebIOSession
from ..utils import random_str, LRUDict

# todo Flask 的线程模型是否会造成竞争条件？
_webio_sessions: Dict[str, WebIOSession] = {}  # WebIOSessionID -> WebIOSession()
_webio_expire = LRUDict()  # WebIOSessionID -> last active timestamp

DEFAULT_SESSION_EXPIRE_SECONDS = 60 * 60 * 4  # 超过4个小时会话不活跃则视为会话过期
REMOVE_EXPIRED_SESSIONS_INTERVAL = 120  # 清理过期会话间隔（秒）

_event_loop = None


def _make_response(webio_session: WebIOSession):
    res = webio_session.unhandled_server_msgs
    webio_session.unhandled_server_msgs = []
    return jsonify(res)


def _remove_expired_sessions(session_expire_seconds):
    while _webio_expire:
        sid, active_ts = _webio_expire.popitem(last=False)
        if time.time() - active_ts < session_expire_seconds:
            _webio_expire[sid] = active_ts
            _webio_expire.move_to_end(sid, last=False)
            break
        del _webio_sessions[sid]


_last_check_session_expire_ts = 0  # 上次检查session有效期的时间戳


def _remove_webio_session(sid):
    del _webio_sessions[sid]
    del _webio_expire[sid]


def _webio_view(coro_func, session_expire_seconds):
    """
    todo use cookie instead of session
    :param coro_func:
    :param session_expire_seconds:
    :return:
    """
    if request.args.get('test'):  # 测试接口，当会话使用给予http的backend时，返回 ok
        return 'ok'

    global _last_check_session_expire_ts, _event_loop
    if _event_loop:
        asyncio.set_event_loop(_event_loop)

    webio_session_id = None
    if 'webio_session_id' not in request.cookies:  # start new WebIOSession
        webio_session_id = random_str(24)
        webio_session = WebIOSession(coro_func)
        _webio_sessions[webio_session_id] = webio_session
        _webio_expire[webio_session_id] = time.time()
    elif request.cookies['webio_session_id'] not in _webio_sessions:  # WebIOSession deleted
        return jsonify([dict(command='close_session')])
    else:
        webio_session_id = request.cookies['webio_session_id']
        webio_session = _webio_sessions[webio_session_id]

    if request.method == 'POST':  # client push event
        webio_session.send_client_msg(request.json)

    elif request.method == 'GET':  # client pull messages
        pass

    if time.time() - _last_check_session_expire_ts > REMOVE_EXPIRED_SESSIONS_INTERVAL:
        _remove_expired_sessions(session_expire_seconds)
        _last_check_session_expire_ts = time.time()

    response = _make_response(webio_session)
    if webio_session.closed():
        _remove_webio_session(webio_session_id)
    elif 'webio_session_id' not in request.cookies:
        response.set_cookie('webio_session_id', webio_session_id)
    return response


def webio_view(coro_func, session_expire_seconds):
    """获取Flask view"""
    view_func = partial(_webio_view, coro_func=coro_func, session_expire_seconds=session_expire_seconds)
    view_func.__name__ = 'webio_view'
    return view_func


def _setup_event_loop():
    global _event_loop
    _event_loop = asyncio.new_event_loop()
    _event_loop.set_debug(True)
    asyncio.set_event_loop(_event_loop)
    _event_loop.run_forever()


def start_flask_server(coro_func, port=8080, host='localhost', disable_asyncio=False,
                       session_expire_seconds=DEFAULT_SESSION_EXPIRE_SECONDS,
                       debug=False, **flask_options):
    """

    :param coro_func:
    :param port:
    :param host:
    :param disable_asyncio: 禁用 asyncio 函数。在Flask backend中使用asyncio需要单独开启一个线程来运行事件循环，
        若程序中没有使用到asyncio中的异步函数，可以开启此选项来避免不必要的资源浪费
    :param session_expire_seconds:
    :param debug:
    :param flask_options:
    :return:
    """
    app = Flask(__name__)
    app.route('/io', methods=['GET', 'POST'])(webio_view(coro_func, session_expire_seconds))

    @app.route('/')
    def index_page():
        return send_from_directory(STATIC_PATH, 'index.html')

    @app.route('/<path:static_file>')
    def serve_static_file(static_file):
        return send_from_directory(STATIC_PATH, static_file)

    if not disable_asyncio:
        threading.Thread(target=_setup_event_loop, daemon=True).start()

    app.run(host=host, port=port, debug=debug, **flask_options)
