import subprocess

from selenium.webdriver import Chrome

import pywebio
import template
import util
from pywebio import start_server
from pywebio.output import *
from pywebio.session import *


def target():
    set_auto_scroll_bottom(False)

    template.basic_output()

    template.background_output()

    hold()


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, debug=True, auto_open_webbrowser=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
