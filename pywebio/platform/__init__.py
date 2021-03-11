r"""
The ``platform`` module provides support for different web frameworks.

See also: :ref:`Integration with Web Framework <integration_web_framework>` section of user manual.

.. versionchanged:: 1.1

   Added the ``cdn`` parameter in ``start_server``, ``webio_handler`` and ``webio_view``.

.. versionchanged:: 1.2

   Added the ``static_dir`` parameter in ``start_server``.

Tornado support
-----------------
.. autofunction:: pywebio.platform.tornado.start_server
.. autofunction:: pywebio.platform.tornado.webio_handler

Flask support
-----------------

When using the Flask as PyWebIO backend server, you need to install Flask by yourself and make sure the version is not less than ``0.10``.
You can install it with the following command::

    pip3 install -U flask>=0.10


.. autofunction:: pywebio.platform.flask.webio_view
.. autofunction:: pywebio.platform.flask.start_server

Django support
-----------------

When using the Django as PyWebIO backend server, you need to install Django by yourself and make sure the version is not less than ``2.2``.
You can install it with the following command::

    pip3 install -U django>=2.2

.. autofunction:: pywebio.platform.django.webio_view
.. autofunction:: pywebio.platform.django.start_server

aiohttp support
-----------------

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