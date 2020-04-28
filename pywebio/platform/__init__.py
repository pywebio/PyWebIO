r"""
``platform`` 模块为PyWebIO提供了对不同Web框架的支持。

Tornado相关
--------------

.. autofunction:: start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

Flask相关
--------------

.. autofunction:: pywebio.platform.flask.webio_view

.. autofunction:: pywebio.platform.flask.start_server

其他
--------------
.. autofunction:: pywebio.platform.httpbased.run_event_loop

"""

from .tornado import start_server
