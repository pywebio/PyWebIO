import subprocess

import time
from percy import percySnapshot
from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio.input import *
from pywebio.output import *
from pywebio.utils import run_as_function
from pywebio.platform.flask import start_server


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
    template.save_output(browser, '4.flask_backend.html')


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
