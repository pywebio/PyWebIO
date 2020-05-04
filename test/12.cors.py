import signal
import subprocess

import time
from selenium.webdriver import Chrome

import template
import util
from pywebio.input import *
from pywebio.utils import run_as_function


def target():
    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


def test_once(browser: Chrome, output_file):
    template.test_output(browser)
    template.test_input(browser)
    time.sleep(1)
    template.save_output(browser, output_file)


def test(server_proc: subprocess.Popen, browser: Chrome):
    test_once(browser, '12.tornado_cors.html')
    server_proc.send_signal(signal.SIGINT)

    time.sleep(4)
    browser.get('http://localhost:5000/?pywebio_api=http://localhost:8081/io')
    test_once(browser, '12.aiohttp_cors.html')
    server_proc.send_signal(signal.SIGINT)

    time.sleep(4)
    browser.get('http://localhost:5000/?pywebio_api=http://localhost:8082/io')
    test_once(browser, '12.flask_cors.html')


def start_test_server():
    from pywebio import start_server as tornado_server
    from pywebio.platform.flask import start_server as flask_server
    from pywebio.platform.aiohttp import start_server as aiohttp_server
    import asyncio

    util.start_static_server()

    try:
        tornado_server(target, port=8080, allowed_origins=['http://localhost:5000'])
    except:
        print('tornado_server exit')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        aiohttp_server(target, port=8081, allowed_origins=['http://localhost:5000'])
    except:
        print('aiohttp_server exit')

    try:
        flask_server(target, port=8082, allowed_origins=['http://localhost:5000'])
    except:
        print('flask_server exit')


if __name__ == '__main__':
    util.run_test(start_test_server, test,
                  address='http://localhost:5000/?pywebio_api=http://localhost:8080/io')
