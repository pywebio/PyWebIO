r"""
The ``platform`` module provides support for different web frameworks.

See also: :ref:`Integration with Web Framework <integration_web_framework>` section of user manual.

Tornado support
-----------------
.. autofunction:: pywebio.platform.tornado.start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

Flask support
-----------------
.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.flask.start_server

Django support
-----------------
.. autofunction:: pywebio.platform.django.webio_view
.. autofunction:: pywebio.platform.django.start_server

aiohttp support
-----------------
.. autofunction:: pywebio.platform.aiohttp.webio_handler
.. autofunction:: pywebio.platform.aiohttp.static_routes
.. autofunction:: pywebio.platform.aiohttp.start_server

Other
--------------
.. autofunction:: pywebio.platform.httpbased.run_event_loop

"""

from .tornado import start_server
