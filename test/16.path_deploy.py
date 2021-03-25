import os
import subprocess

from percy import percySnapshot
from selenium.webdriver import Chrome

import util
from pywebio.platform import path_deploy
from pywebio.utils import *
import template

here_dir = os.path.dirname(os.path.abspath(__file__))
demos_dir = os.path.join(here_dir, '..', 'demos')


def test(server_proc: subprocess.Popen, browser: Chrome):
    time.sleep(10)
    percySnapshot(browser, name='path_deploy_1')
    browser.get('http://localhost:8080/')
    time.sleep(2)
    page_html = browser.find_element_by_tag_name('body').get_attribute('innerHTML')
    for f in ['bmi', 'bokeh_app', 'chat_room', 'doc_demo', 'input_usage', 'output_usage', 'set_env_demo']:
        assert f in page_html

    time.sleep(2)


def start_test_server():
    path_deploy(demos_dir, port=8080, host='127.0.0.1', cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test, address='http://localhost:8080/bokeh_app')
