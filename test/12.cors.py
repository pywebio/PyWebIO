import signal
import subprocess

import time
from selenium.webdriver import Chrome

import template
import util
from pywebio.input import *
from pywebio.utils import run_as_function
from pywebio.session import run_js


def target():
    run_js("$('#markdown-body>.alert-warning').remove()")
    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


def test_once(browser: Chrome, output_file, process_func):
    template.test_output(browser)
    template.test_input(browser)
    time.sleep(1)
    return template.save_output(browser, output_file, process_func)[0]


def test(server_proc: subprocess.Popen, browser: Chrome):
    raw_html = test_once(browser, '12.tornado_cors.html',
                         process_func=lambda i: i.replace('http://localhost:5000', 'http://localhost:8080'))
    assert 'http://localhost:5000' in raw_html  # origin
    server_proc.send_signal(signal.SIGINT)

    time.sleep(4)
    browser.get('http://localhost:5000/?pywebio_api=http://localhost:8081/')
    raw_html = test_once(browser, '12.aiohttp_cors.html',
                         process_func=lambda i: i.replace('http://localhost:5000', 'http://localhost:8080').replace(
                             'localhost:8081', 'localhost:8080'))
    assert 'http://localhost:5000' in raw_html and 'localhost:8081' in raw_html  # origin
    server_proc.send_signal(signal.SIGINT)

    time.sleep(4)
    browser.get('http://localhost:5000/?pywebio_api=http://localhost:8082/')
    raw_html = test_once(browser, '12.flask_cors.html',
                         process_func=lambda i: i.replace('http://localhost:5000', 'http://localhost:8080').replace(
                             'localhost:8082', 'localhost:8080'))
    assert 'http://localhost:5000' in raw_html and 'localhost:8082' in raw_html  # origin


def start_test_server():
    from pywebio import start_server as tornado_server
    from pywebio.platform.flask import start_server as flask_server
    from pywebio.platform.aiohttp import start_server as aiohttp_server
    import asyncio

    util.start_static_server()

    try:
        tornado_server(target, port=8080, host='127.0.0.1', allowed_origins=['http://localhost:5000'], cdn=False)
    except:
        print('tornado_server exit')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        aiohttp_server(target, port=8081, host='127.0.0.1', allowed_origins=['http://localhost:5000'], cdn=False)
    except:
        print('aiohttp_server exit')

    try:
        flask_server(target, port=8082, host='127.0.0.1', allowed_origins=['http://localhost:5000'], cdn=False)
    except:
        print('flask_server exit')


if __name__ == '__main__':
    util.run_test(start_test_server, test,
                  address='http://localhost:5000/?pywebio_api=http://localhost:8080/')
