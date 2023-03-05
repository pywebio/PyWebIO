import abc
import asyncio
import json
import logging
import time
import typing
from typing import Dict, Optional

from ...session import CoroutineBasedSession, Session, ThreadBasedSession
from ...utils import LRUDict, iscoroutinefunction, isgeneratorfunction, random_str
from ..utils import deserialize_binary_event

logger = logging.getLogger(__name__)


# used to store global state when reconnect enabled
class _reconnect_state:
    # used to clean up session
    detached_sessions = LRUDict()  # session_id -> detached timestamp. In increasing order of the time

    # unclosed and unexpired session
    # used to clean up session
    # used to retrieve session by id when new connection
    unclosed_sessions: Dict[str, Session] = {}  # session_id -> session

    # the messages that can't deliver to browser when session close due to connection lost
    session_will_messages: Dict[str, list] = {}  # session_id -> unhandled message list

    # used to get the active conn in session's callbacks
    active_connections: Dict[str, 'WebSocketConnection'] = {}  # session_id -> WSHandler

    expire_second = 0


def set_expire_second(sec):
    _reconnect_state.expire_second = max(_reconnect_state.expire_second, sec)


def clean_expired_sessions():
    while _reconnect_state.detached_sessions:
        session_id, detached_ts = _reconnect_state.detached_sessions.popitem(last=False)  # 弹出最早过期的session

        if time.time() < detached_ts + _reconnect_state.expire_second:
            # this session is not expired
            _reconnect_state.detached_sessions[session_id] = detached_ts  # restore
            _reconnect_state.detached_sessions.move_to_end(session_id, last=False)  # move to head
            break

        # clean this session
        logger.debug("session %s expired" % session_id)
        _reconnect_state.active_connections.pop(session_id, None)
        _reconnect_state.session_will_messages.pop(session_id, None)
        session = _reconnect_state.unclosed_sessions.pop(session_id, None)
        if session:
            session.close(nonblock=True)


_session_clean_task_started = False


async def session_clean_task():
    global _session_clean_task_started
    if _session_clean_task_started or not _reconnect_state.expire_second:
        return

    _session_clean_task_started = True
    logger.debug("Start session cleaning task")
    while True:
        try:
            clean_expired_sessions()
        except Exception:
            logger.exception("Error when clean expired sessions")

        await asyncio.sleep(_reconnect_state.expire_second // 2)


class WebSocketConnection(abc.ABC):
    @abc.abstractmethod
    def get_query_argument(self, name) -> typing.Optional[str]:
        pass

    @abc.abstractmethod
    def make_session_info(self) -> dict:
        pass

    @abc.abstractmethod
    def write_message(self, message: dict):
        pass

    @abc.abstractmethod
    def closed(self) -> bool:
        return False

    @abc.abstractmethod
    def close(self):
        pass


class WebSocketHandler:
    """
    hold by one connection,
    share one session with multiple connection in session lifetime, but one conn at a time
    """

    session_id: Optional[str] = None
    session: Optional[Session] = None  # the session that current connection attaches
    connection: WebSocketConnection
    reconnectable: bool

    def __init__(self, connection: WebSocketConnection, application, reconnectable: bool, ioloop=None):
        logger.debug("WebSocket opened")
        self.connection = connection
        self.reconnectable = reconnectable
        self.session_id = connection.get_query_argument('session')
        self.ioloop = ioloop or asyncio.get_event_loop()

        if self.session_id in ('NEW', None):  # 初始请求，创建新 Session
            self._init_session(application)
            if reconnectable:
                _reconnect_state.active_connections[self.session_id] = self.connection
                _reconnect_state.unclosed_sessions[self.session_id] = self.session
                # set session id to client, so the client can send it back to server to recover a session when it
                # resumes form a connection lost
                connection.write_message(dict(command='set_session_id', spec=self.session_id))
        elif self.session_id not in _reconnect_state.unclosed_sessions:  # session is expired
            bye_msg = dict(command='close_session')
            for m in _reconnect_state.session_will_messages.get(self.session_id, [bye_msg]):
                try:
                    connection.write_message(m)
                except Exception:
                    logger.exception("Error in sending message via websocket")
        else:  # resumes form a connection lost
            self.session = _reconnect_state.unclosed_sessions[self.session_id]
            _reconnect_state.detached_sessions.pop(self.session_id, None)
            _reconnect_state.active_connections[self.session_id] = connection
            # send the latest messages to client
            self._send_msg_to_client()

        logger.debug('session id: %s' % self.session_id)

    def _init_session(self, application):
        session_info = self.connection.make_session_info()
        self.session_id = random_str(24)

        if iscoroutinefunction(application) or isgeneratorfunction(application):
            self.session = CoroutineBasedSession(
                application, session_info=session_info,
                on_task_command=self._send_msg_to_client,
                on_session_close=self._close_from_session)
        else:
            self.session = ThreadBasedSession(
                application, session_info=session_info,
                on_task_command=self._send_msg_to_client,
                on_session_close=self._close_from_session,
                loop=self.ioloop)

    def _get_active_connection(self) -> Optional[WebSocketConnection]:
        # when reconnect enabled, the active connection for this session is in _reconnect_state.active_connections,
        # otherwise, it's self.connection.
        if self.reconnectable:
            conn = _reconnect_state.active_connections.get(self.session_id)
        else:
            conn = self.connection

        return conn

    def _send_msg_to_client(self, session: Session = None):
        conn = self._get_active_connection()
        session = session or self.session

        if not conn or conn.closed():
            return

        for msg in session.get_task_commands():
            try:
                conn.write_message(msg)
            except TypeError as e:
                logger.exception('Data serialization error: %s\n'
                                 'This may be because you pass the wrong type of parameter to the function'
                                 ' of PyWebIO.\nData content: %s', e, msg)
            except Exception:
                logger.exception("Error in sending message via websocket")

    def _close_from_session(self):
        conn = self._get_active_connection()
        if conn and not conn.closed():
            self._send_msg_to_client()
            conn.close()
        elif self.reconnectable:  # no active connection, and reconnect is enabled
            _reconnect_state.session_will_messages[self.session_id] = self.session.get_task_commands()
        self.session = None

    def send_client_data(self, data):
        if isinstance(data, bytes):
            event = deserialize_binary_event(data)
        else:
            event = json.loads(data)
        if event is None:
            return
        self.session.send_client_event(event)

    def notify_connection_lost(self):
        logger.debug("WebSocket closed")
        if not self.reconnectable and self.session:
            # when the connection lost is caused by `on_session_close()`, it's OK to close the session here though.
            # because the `session.close()` is reentrant
            self.session.close(nonblock=True)
            self.session = None  # reset the reference
            return

        _reconnect_state.active_connections.pop(self.session_id, None)
        if self.session_id in _reconnect_state.unclosed_sessions:
            _reconnect_state.detached_sessions[self.session_id] = time.time()
