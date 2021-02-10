import subprocess
import time

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.platform.django import start_server
from pywebio.utils import run_as_function


def target():
    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)

    time.sleep(1)

    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '3.django_backend.html')


def start_test_server():
    pywebio.enable_debug()

    start_server(target, port=8080, host='127.0.0.1', cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
