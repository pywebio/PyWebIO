r"""
``platform`` 模块为PyWebIO提供了对不同Web框架的支持。

具体用法参见用户手册 :ref:`与Web框架集成 <integration_web_framework>` 小节

Tornado相关
--------------
.. autofunction:: pywebio.platform.tornado.start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

Flask相关
--------------
.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.flask.start_server

Django相关
--------------
.. autofunction:: pywebio.platform.django.webio_view
.. autofunction:: pywebio.platform.django.start_server

aiohttp相关
--------------
.. autofunction:: pywebio.platform.aiohttp.webio_handler
.. autofunction:: pywebio.platform.aiohttp.start_server

其他
--------------
.. autofunction:: pywebio.platform.seo
.. autofunction:: pywebio.platform.run_event_loop

"""

from .httpbased import run_event_loop
from .tornado import start_server
from .utils import seo