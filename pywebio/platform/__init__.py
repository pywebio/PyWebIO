r"""
``platform`` 模块为PyWebIO提供了对不同Web框架的支持。

Tornado相关
--------------

.. autofunction:: start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

Flask相关
--------------

.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.flask.run_event_loop
.. autofunction:: pywebio.platform.flask.start_server


"""

from . import tornado
from .tornado import start_server

try:
    from . import flask
except ImportError:
    pass

