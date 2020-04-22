import subprocess

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio import start_server
from pywebio.input import actions
from pywebio.output import *
from pywebio.utils import run_as_function


def target():
    set_auto_scroll_bottom(True)

    template.set_defer_call()

    run_as_function(template.basic_input())

    actions(buttons=['Continue'])

    template.background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_input(browser)
    template.test_defer_call()


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, debug=False, auto_open_webbrowser=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
