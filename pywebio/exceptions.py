"""
pywebio.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of PyWebIO's exceptions.
"""


class SessionException(Exception):
    pass


class SessionClosedException(SessionException):
    pass


class SessionNotFoundException(SessionException):
    pass
