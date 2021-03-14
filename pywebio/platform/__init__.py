r"""
The ``platform`` module provides support for deploying PyWebIO applications in different web frameworks.

.. seealso::

   * :ref:`Integration with Web Framework <integration_web_framework>`

   * :ref:`Server mode and Script mode <server_and_script_mode>`

Directory Deploy
-----------------

You can use ``path_deploy()`` or ``path_deploy_http()`` to deploy the PyWebIO applications from a directory.
You can access the application by using the file path as the URL.

.. autofunction:: pywebio.platform.path_deploy
.. autofunction:: pywebio.platform.path_deploy_http

Application Deploy
--------------------

The ``start_server()`` functions can start a Python Web server and serve given PyWebIO applications on it.

The ``webio_handler()`` and ``webio_view()`` functions can be used to integrate PyWebIO applications into existing Python Web project.

.. versionchanged:: 1.1

   Added the ``cdn`` parameter in ``start_server()``, ``webio_handler()`` and ``webio_view()``.

.. versionchanged:: 1.2

   Added the ``static_dir`` parameter in ``start_server()``.

Tornado support
^^^^^^^^^^^^^^^^^^^^

There are two protocols (WebSocket and HTTP) can be used to communicates with the browser:

WebSocket
'''''''''''''

.. autofunction:: pywebio.platform.tornado.start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

HTTP
'''''''''''''

.. autofunction:: pywebio.platform.tornado_http.start_server
.. autofunction:: pywebio.platform.tornado_http.webio_handler


Flask support
^^^^^^^^^^^^^^^^^^^^

When using the Flask as PyWebIO backend server, you need to install Flask by yourself and make sure the version is not less than ``0.10``.
You can install it with the following command::

    pip3 install -U flask>=0.10


.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.flask.start_server

Django support
^^^^^^^^^^^^^^^^^^^^

When using the Django as PyWebIO backend server, you need to install Django by yourself and make sure the version is not less than ``2.2``.
You can install it with the following command::

    pip3 install -U django>=2.2

.. autofunction:: pywebio.platform.django.webio_view
.. autofunction:: pywebio.platform.django.start_server

aiohttp support
^^^^^^^^^^^^^^^^^^^^

When using the aiohttp as PyWebIO backend server, you need to install aiohttp by yourself and make sure the version is not less than ``3.1``.
You can install it with the following command::

    pip3 install -U aiohttp>=3.1

.. autofunction:: pywebio.platform.aiohttp.webio_handler
.. autofunction:: pywebio.platform.aiohttp.start_server

Other
--------------
.. autofunction:: pywebio.platform.seo
.. autofunction:: pywebio.platform.run_event_loop

"""

from .httpbased import run_event_loop
from .tornado import start_server
from .utils import seo
from .path_deploy import path_deploy_http, path_deploy