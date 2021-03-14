import os
import subprocess

from percy import percySnapshot
from selenium.webdriver import Chrome

import util
from pywebio.platform import path_deploy
from pywebio.utils import *


def test(server_proc: subprocess.Popen, browser: Chrome):
    time.sleep(6)
    percySnapshot(browser, name='path_deploy_1')
    time.sleep(2)
    browser.get('http://localhost:8080/')
    time.sleep(2)
    percySnapshot(browser, name='path_deploy_index')
    time.sleep(2)


def start_test_server():
    here_dir = os.path.dirname(os.path.abspath(__file__))

    path_deploy(here_dir + '/../demos', port=8080, host='127.0.0.1', cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test, address='http://localhost:8080/bokeh_app')
