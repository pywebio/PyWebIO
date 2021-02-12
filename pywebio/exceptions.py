"""
pywebio.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of PyWebIO's exceptions.
"""


class SessionException(Exception):
    """Base class for PyWebIO session related exceptions"""


class SessionClosedException(SessionException):
    """The session has been closed abnormally"""


class SessionNotFoundException(SessionException):
    """Session not found"""


class PyWebIOWarning(UserWarning):
    pass
