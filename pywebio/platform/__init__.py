r"""
platform 模块为PyWebIO提供了对不同Web框架的支持。

你可以启动使用不同Web框架的Server，或者获得整合进现有Web框架的必要数据。


.. autofunction:: start_server
.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.tornado.webio_handler

"""

from . import tornado
from .tornado import start_server

try:
    from . import flask
except ModuleNotFoundError:
    pass

