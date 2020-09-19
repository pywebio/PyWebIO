"""
pywebio.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of PyWebIO's exceptions.
"""


class SessionException(Exception):
    """PyWebIO会话相关异常的基类"""


class SessionClosedException(SessionException):
    """会话已经关闭异常"""


class SessionNotFoundException(SessionException):
    """会话未找到异常"""

