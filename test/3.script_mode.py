import os
import subprocess

import time
from percy import percySnapshot
from selenium.webdriver import Chrome

import template
import util
from pywebio.input import *
from pywebio.output import *
from pywebio.utils import run_as_function


def target():
    set_auto_scroll_bottom(True)

    template.basic_output()

    template.background_output()

    run_as_function(template.basic_input())

    actions(buttons=['Continue'])

    template.background_input()


def test(server_proc: subprocess.Popen, browser: Chrome):
    percy_prefix = '[script_mode]'

    template.test_output(browser, percy_prefix=percy_prefix)

    time.sleep(1)

    template.test_input(browser, percy_prefix=percy_prefix)

    # script mode 下，此时 server 应停止
    server_proc.wait(timeout=8)
    percySnapshot(browser=browser, name=percy_prefix + 'over')


if __name__ == '__main__':
    # 设置监听端口，并关闭自动打开浏览器
    os.environ["PYWEBIO_SCRIPT_MODE_PORT"] = "8080"

    util.run_test(target, test)
