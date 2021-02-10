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
    template.save_output(browser, '8.flask_multiple_session_impliment_p1.html')

    browser.get('http://localhost:8080/io2?_pywebio_debug=1&_pywebio_http_pull_interval=400')
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '8.flask_multiple_session_impliment_p2.html')


def start_test_server():
    pywebio.enable_debug()
    from flask import Flask, send_from_directory
    from pywebio.platform.flask import webio_view, run_event_loop
    from pywebio import STATIC_PATH
    import threading
    import logging

    app = Flask(__name__)
    app.add_url_rule('/io', 'webio_view', webio_view(target, cdn=False), methods=['GET', 'POST', 'OPTIONS'])
    app.add_url_rule('/io2', 'webio_view_async_target', webio_view(async_target, cdn=False), methods=['GET', 'POST', 'OPTIONS'])

    @app.route('/')
    @app.route('/<path:static_file>')
    def serve_static_file(static_file='index.html'):
        return send_from_directory(STATIC_PATH, static_file)

    threading.Thread(target=run_event_loop, daemon=True).start()

    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    app.run(port=8080, host='127.0.0.1')


if __name__ == '__main__':
    util.run_test(start_test_server, test, address='http://localhost:8080/io?_pywebio_debug=1&_pywebio_http_pull_interval=400')
