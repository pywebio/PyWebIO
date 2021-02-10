import subprocess
import time

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.platform.flask import start_server
from pywebio.utils import to_coroutine


async def target():
    template.basic_output()
    await template.coro_background_output()

    await to_coroutine(template.basic_input())
    await actions(buttons=['Continue'])
    await template.flask_coro_background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)

    time.sleep(1)

    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '6.flask_coroutine.html')


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, host='127.0.0.1', cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test, address='http://localhost:8080?_pywebio_debug=1&_pywebio_http_pull_interval=400')
