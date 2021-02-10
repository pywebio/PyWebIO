import subprocess
import time

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.utils import to_coroutine, run_as_function


def target():
    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


async def async_target():
    template.basic_output()
    await template.coro_background_output()

    await to_coroutine(template.basic_input())
    await actions(buttons=['Continue'])
    await template.coro_background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)
    time.sleep(1)
    template.save_output(browser, '14.flask_multiple_session_impliment_p1.html')

    browser.get('http://localhost:8080/app2?_pywebio_debug=1&_pywebio_http_pull_interval=400')
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '14.flask_multiple_session_impliment_p2.html')


urlpatterns = []


def start_test_server():
    global urlpatterns

    pywebio.enable_debug()
    from functools import partial
    from pywebio.platform.django import webio_view
    from django.conf import settings
    from django.core.wsgi import get_wsgi_application
    from django.urls import path
    from django.utils.crypto import get_random_string
    from django.views.static import serve
    from pywebio import STATIC_PATH

    django_options = dict(
        DEBUG=True,
        ALLOWED_HOSTS=["*"],  # Disable host header validation
        ROOT_URLCONF=__name__,  # Make this module the urlconf
        SECRET_KEY=get_random_string(10),  # We aren't using any security features but Django requires this setting
    )
    django_options.setdefault('LOGGING', {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '[%(asctime)s] %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
        },
        'loggers': {
            'django.server': {
                'level': 'INFO',
                'handlers': ['console'],
            },
        },
    })
    settings.configure(**django_options)

    urlpatterns = [
        path(r"app", webio_view(target, cdn=False)),
        path(r"app2", webio_view(async_target, cdn=False)),
        path(r'', partial(serve, path='index.html'), {'document_root': STATIC_PATH}),
        path(r'<path:path>', serve, {'document_root': STATIC_PATH}),
    ]

    app = get_wsgi_application()  # load app

    import tornado.wsgi
    container = tornado.wsgi.WSGIContainer(app)
    http_server = tornado.httpserver.HTTPServer(container)
    http_server.listen(8080, address='127.0.0.1')
    tornado.ioloop.IOLoop.current().start()


if __name__ == '__main__':
    util.run_test(start_test_server, test,
                  address='http://localhost:8080/app?_pywebio_debug=1&_pywebio_http_pull_interval=400')
