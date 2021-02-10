import subprocess
import time

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio import start_server
from pywebio.input import *
from pywebio.session import set_env
from pywebio.utils import run_as_function


def target():
    set_env(auto_scroll_bottom=True)
    template.set_defer_call()

    template.basic_output()
    template.background_output()

    run_as_function(template.basic_input())
    actions(buttons=['Continue'])
    template.background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser, enable_percy=True)

    template.test_input(browser, enable_percy=True)

    time.sleep(1)
    template.save_output(browser, '1.basic.html')

    template.test_defer_call()


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, host='127.0.0.1', auto_open_webbrowser=False, cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
