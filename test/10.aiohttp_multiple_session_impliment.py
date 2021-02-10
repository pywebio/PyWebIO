import subprocess
import time

from aiohttp import web
from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.platform.aiohttp import static_routes, webio_handler
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
    template.save_output(browser, '10.aiohttp_multiple_session_impliment_p1.html')

    browser.get('http://localhost:8080/io2?_pywebio_debug=1')
    template.test_output(browser)
    time.sleep(1)
    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '10.aiohttp_multiple_session_impliment_p2.html')


def start_test_server():
    pywebio.enable_debug()

    app = web.Application()
    app.add_routes([web.get('/io', webio_handler(target, cdn=False))])
    app.add_routes([web.get('/io2', webio_handler(async_target, cdn=False))])
    app.add_routes(static_routes())

    web.run_app(app, host='127.0.0.1', port=8080)


if __name__ == '__main__':
    util.run_test(start_test_server, test, 'http://localhost:8080/io?_pywebio_debug=1')
