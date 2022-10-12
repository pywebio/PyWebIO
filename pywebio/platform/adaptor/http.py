"""
本模块提供基于Http轮训的后端通用类和函数

.. attention::
    PyWebIO 的会话状态保存在进程内，基于HTTP的会话不支持多进程部署的后端服务
    比如使用 ``uWSGI`` 部署后端服务，并使用 ``--processes n`` 选项设置了多进程；
    或者使用 ``nginx`` 等反向代理将流量负载到多个后端副本上。

"""
import asyncio
import fnmatch
import json
import logging
import threading
import time
from contextlib import contextmanager
from typing import Dict

from ..page import make_applications, render_page
from ..utils import deserialize_binary_event
from ...session import CoroutineBasedSession, Session, ThreadBasedSession, register_session_implement_for_target
from ...session.base import get_session_info_from_headers
from ...utils import random_str, LRUDict, isgeneratorfunction, iscoroutinefunction, check_webio_js


class HttpContext:
    """一次Http请求的上下文， 不同的后端框架需要根据框架提供的方法实现本类的方法

    The context of an Http request"""

    backend_name = ''  # 当前使用的Web框架名

    def request_obj(self):
        """返回当前请求对象
        Return the current request object"""
        pass

    def request_method(self):
        """返回当前请求的方法，大写
        Return the HTTP method of the current request, uppercase"""
        pass

    def request_headers(self) -> dict:
        """返回当前请求的header字典
        Return the header dictionary of the current request"""
        pass

    def request_url_parameter(self, name, default=None):
        """返回当前请求的URL参数
        Returns the value of the given URL parameter of the current request"""
        pass

    def request_body(self):
        """返回当前请求的body数据
        Returns the data of the current request body

        :return: bytes/bytearray
        """
        return b''

    def request_json(self) -> dict:
        """返回当前请求的json反序列化后的内容，若请求数据不为json格式，返回None
        Return the data (json deserialization) of the currently requested, if the data is not in json format, return None"""
        try:
            if self.request_headers().get('content-type') == 'application/octet-stream':
                return deserialize_binary_event(self.request_body())
            return json.loads(self.request_body())
        except Exception:
            return None

    def set_header(self, name, value):
        """为当前响应设置header
        Set a header for the current response"""
        pass

    def set_status(self, status):
        """为当前响应设置http status
        Set http status for the current response"""
        pass

    def set_content(self, content, json_type=False):
        """设置响应的内容。方法应该仅被调用一次
        Set the content of the response. This method should only be called once

        :param str/bytes/json-able content:
        :param bool json_type: Whether to serialize content into json str and set content-type to application/json
        """
        pass

    def get_response(self):
        """获取当前的响应对象，用于在视图函数中返回
        Get the current response object"""
        pass

    def get_client_ip(self):
        """获取用户的ip
        Get the user's ip"""
        pass


logger = logging.getLogger(__name__)
_event_loop = None


# todo: use lock to avoid thread race condition
class HttpHandler:
    """基于HTTP的后端Handler实现

    .. note::
        Don't need a lock when access HttpHandler._webio_sessions, See：
        https://stackoverflow.com/questions/1312331/using-a-global-dictionary-with-threads-in-python

    """
    # type: Dict[str, Session]
    _webio_sessions = {}  # WebIOSessionID -> WebIOSession()
    _webio_last_commands = {}  # WebIOSessionID -> (last commands, commands sequence id)
    _webio_expire = LRUDict()  # WebIOSessionID -> last active timestamp. In increasing order of last active time
    _webio_expire_lock = threading.Lock()

    _last_check_session_expire_ts = 0  # Timestamp of the last check session validation

    # After processing the POST request, wait for WAIT_MS_ON_POST milliseconds before generate response
    WAIT_MS_ON_POST = 100

    DEFAULT_SESSION_EXPIRE_SECONDS = 600  # Default session expiration time
    DEFAULT_SESSIONS_CLEANUP_INTERVAL = 300  # Default interval for clearing expired sessions (in seconds)

    @classmethod
    def _remove_expired_sessions(cls, session_expire_seconds):
        """清除当前会话列表中的过期会话"""
        logger.debug("removing expired sessions")
        while cls._webio_expire:
            sid, active_ts = cls._webio_expire.popitem(last=False)  # 弹出最不活跃的session info

            if time.time() - active_ts < session_expire_seconds:
                # this session is not expired
                cls._webio_expire[sid] = active_ts
                cls._webio_expire.move_to_end(sid, last=False)
                break

            # clean this session
            logger.debug("session %s expired" % sid)
            session = cls._webio_sessions.get(sid)
            if session:
                session.close(nonblock=True)
                del cls._webio_sessions[sid]

    @classmethod
    def _remove_webio_session(cls, sid):
        cls._webio_sessions.pop(sid, None)
        cls._webio_expire.pop(sid, None)

    @classmethod
    def get_response(cls, sid, ack=0):
        commands, seq = cls._webio_last_commands.get(sid, ([], 0))
        if ack == seq:
            webio_session = cls._webio_sessions[sid]
            commands = webio_session.get_task_commands()
            seq += 1
            cls._webio_last_commands[sid] = (commands, seq)

        return {'commands': commands, 'seq': seq}

    def _process_cors(self, context: HttpContext):
        """Handling cross-domain requests: check the source of the request and set headers"""
        origin = context.request_headers().get('Origin', '')
        if self.check_origin(origin):
            context.set_header('Access-Control-Allow-Origin', origin)
            context.set_header('Access-Control-Allow-Methods', 'GET, POST')
            context.set_header('Access-Control-Allow-Headers', 'content-type, webio-session-id')
            context.set_header('Access-Control-Expose-Headers', 'webio-session-id')
            context.set_header('Access-Control-Max-Age', str(1440 * 60))

    def interval_cleaning(self):
        # clean up at intervals
        cls = type(self)
        need_clean = False

        if time.time() - cls._last_check_session_expire_ts > self.session_cleanup_interval:
            with cls._webio_expire_lock:
                if time.time() - cls._last_check_session_expire_ts > self.session_cleanup_interval:
                    cls._last_check_session_expire_ts = time.time()
                    need_clean = True

        if need_clean:
            cls._remove_expired_sessions(self.session_expire_seconds)

    def handle_request(self, context: HttpContext):
        try:
            with self.handle_request_context(context) as sleep_dur:
                if sleep_dur:
                    time.sleep(sleep_dur)
        except RuntimeError:
            pass

        return context.get_response()

    async def handle_request_async(self, context: HttpContext):
        try:
            with self.handle_request_context(context) as sleep_dur:
                if sleep_dur:
                    await asyncio.sleep(sleep_dur)
        except RuntimeError:
            pass

        return context.get_response()

    def get_cdn(self, context):
        if self.cdn is True and context.request_url_parameter('_pywebio_cdn', '') == 'false':
            return False
        return self.cdn

    @contextmanager
    def handle_request_context(self, context: HttpContext):
        """called when every http request"""
        cls = type(self)

        if _event_loop:
            asyncio.set_event_loop(_event_loop)

        request_headers = context.request_headers()

        # CORS process start ############################
        if context.request_method() == 'OPTIONS':  # preflight request for CORS
            self._process_cors(context)
            context.set_status(204)
            return context.get_response()

        if request_headers.get('Origin'):  # set headers for CORS request
            self._process_cors(context)
        # CORS process end ############################

        if context.request_url_parameter('test'):  # 测试接口，当会话使用基于http的backend时，返回 ok
            context.set_content('ok')
            return context.get_response()

        # 对首页HTML的请求
        if 'webio-session-id' not in request_headers:
            app = self.app_loader(context)
            html = render_page(app, protocol='http', cdn=self.get_cdn(context))
            context.set_content(html)
            return context.get_response()

        webio_session_id = None

        # 初始请求，创建新 Session
        if not request_headers['webio-session-id'] or request_headers['webio-session-id'] == 'NEW':
            if context.request_method() == 'POST':  # 不能在POST请求中创建Session，防止CSRF攻击
                context.set_status(403)
                return context.get_response()

            webio_session_id = random_str(24)
            context.set_header('webio-session-id', webio_session_id)
            session_info = get_session_info_from_headers(context.request_headers())
            session_info['user_ip'] = context.get_client_ip()
            session_info['request'] = context.request_obj()
            session_info['backend'] = context.backend_name
            session_info['protocol'] = 'http'

            application = self.app_loader(context)

            if iscoroutinefunction(application) or isgeneratorfunction(application):
                session_cls = CoroutineBasedSession
            else:
                session_cls = ThreadBasedSession
            webio_session = session_cls(application, session_info=session_info)
            cls._webio_sessions[webio_session_id] = webio_session
            yield type(self).WAIT_MS_ON_POST / 1000.0  # <--- <--- <--- <--- <--- <--- <--- <--- <--- <--- <--- <---
        elif request_headers['webio-session-id'] not in cls._webio_sessions:  # WebIOSession deleted
            context.set_content([dict(command='close_session')], json_type=True)
            return context.get_response()
        else:
            webio_session_id = request_headers['webio-session-id']
            webio_session = cls._webio_sessions[webio_session_id]

        if context.request_method() == 'POST':  # client push event
            if context.request_json() is not None:
                webio_session.send_client_event(context.request_json())
                yield type(self).WAIT_MS_ON_POST / 1000.0  # <--- <--- <--- <--- <--- <--- <--- <--- <--- <--- <--- <---
        elif context.request_method() == 'GET':  # client pull messages
            pass

        cls._webio_expire[webio_session_id] = time.time()

        self.interval_cleaning()

        ack = int(context.request_url_parameter('ack', 0))
        context.set_content(type(self).get_response(webio_session_id, ack=ack), json_type=True)

        if webio_session.closed():
            self._remove_webio_session(webio_session_id)

        return context.get_response()

    def __init__(self, applications=None, app_loader=None,
                 cdn=True,
                 session_expire_seconds=None,
                 session_cleanup_interval=None,
                 allowed_origins=None, check_origin=None):
        """Get the view function for running PyWebIO applications in Web framework.
        The view communicates with the client by HTTP protocol.

        :param callable app_loader: PyWebIO app factory, which receives the HttpContext instance as the parameter.
            Can not use `app_loader` and `applications` at the same time.

        The rest arguments of the constructor have the same meaning as for :func:`pywebio.platform.flask.start_server()`
        """
        check_webio_js()

        cls = type(self)

        self.cdn = cdn
        self.check_origin = check_origin
        self.session_expire_seconds = session_expire_seconds or cls.DEFAULT_SESSION_EXPIRE_SECONDS
        self.session_cleanup_interval = session_cleanup_interval or cls.DEFAULT_SESSIONS_CLEANUP_INTERVAL

        assert applications is not None or app_loader is not None
        if applications is not None:
            applications = make_applications(applications)

        def get_app(context):
            app_name = context.request_url_parameter('app', 'index')
            return applications.get(app_name) or applications['index']

        self.app_loader = app_loader or get_app

        for target in (applications or {}).values():
            register_session_implement_for_target(target)

        if check_origin is None:
            self.check_origin = lambda origin: any(
                fnmatch.fnmatch(origin, pattern)
                for pattern in (allowed_origins or [])
            )


def run_event_loop(debug=False):
    """run asyncio event loop

    See also: :ref:`Integration coroutine-based session with Web framework <coroutine_web_integration>`

    :param debug: Set the debug mode of the event loop.
       See also: https://docs.python.org/3/library/asyncio-dev.html#asyncio-debug-mode
    """
    global _event_loop
    CoroutineBasedSession.event_loop_thread_id = threading.current_thread().ident
    _event_loop = asyncio.new_event_loop()
    _event_loop.set_debug(debug)
    asyncio.set_event_loop(_event_loop)
    _event_loop.run_forever()
