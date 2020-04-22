import subprocess

from selenium.webdriver import Chrome

import pywebio
import template
import time
import util
from pywebio.input import *
from pywebio.output import *
from pywebio.utils import to_coroutine, run_as_function


def target():
    set_auto_scroll_bottom(False)

    template.basic_output()

    template.background_output()

    run_as_function(template.basic_input())

    actions(buttons=['Continue'])

    template.background_input()


async def async_target():
    set_auto_scroll_bottom(False)

    template.basic_output()

    await template.coro_background_output()

    await to_coroutine(template.basic_input())

    await actions(buttons=['Continue'])

    await template.coro_background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):

    template.test_output(browser, percy_prefix='[multi flask coro]')

    time.sleep(1)

    template.test_input(browser, percy_prefix='[multi flask coro]')

    time.sleep(3)

    browser.get('http://localhost:8080?_pywebio_debug=1&pywebio_api=io2')

    template.test_output(browser, percy_prefix='[multi flask thread]')

    time.sleep(1)

    template.test_input(browser, percy_prefix='[multi flask thread]')


def start_test_server():
    pywebio.enable_debug()
    from flask import Flask, send_from_directory
    from pywebio.platform.flask import webio_view, run_event_loop
    from pywebio import STATIC_PATH
    import threading
    import logging

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(target), methods=['GET', 'POST', 'OPTIONS'])
    app.add_url_rule('/io2', 'webio_view_async_target', webio_view(async_target), methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    threading.Thread(target=run_event_loop, daemon=True).start()

    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    app.run(port=8080)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
