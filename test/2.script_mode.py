import os
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


def test(server_proc: subprocess.Popen, browser: Chrome):
    template.test_output(browser)

    time.sleep(1)

    template.test_input(browser)

    time.sleep(1)
    template.save_output(browser, '2.script_mode.html',
                         # because tornado default bind ipv4 and ipv6 in script mode
                         process_func=lambda i: i.replace('::1', '127.0.0.1'))

    browser.close()
    time.sleep(3)

    # script mode 下，此时 server 应停止
    server_proc.wait(timeout=8)


if __name__ == '__main__':
    # 设置监听端口，并关闭自动打开浏览器
    os.environ["PYWEBIO_SCRIPT_MODE_PORT"] = "8080"

    util.run_test(target, test)
