from .base import AbstractSession
from .asyncbased import AsyncBasedSession
from .threadbased import ThreadBasedWebIOSession

_session_type = AsyncBasedSession


def set_session_implement(session_type):
    global _session_type
    assert session_type in [ThreadBasedWebIOSession, AsyncBasedSession]
    _session_type = session_type


def get_session_implement():
    global _session_type
    return _session_type


def get_current_session() -> "AbstractSession":
    return _session_type.get_current_session()


def get_current_task_id():
    return _session_type.get_current_task_id()
