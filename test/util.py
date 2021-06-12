import asyncio
import signal
import subprocess
import sys
import threading
from functools import partial
from urllib.parse import urlparse

from selenium import webdriver

from pywebio import STATIC_PATH
from pywebio.utils import wait_host_port

default_chrome_options = webdriver.ChromeOptions()
default_chrome_options.add_argument('--no-sandbox')
default_chrome_options.add_argument('--disable-extensions')
default_chrome_options.add_argument('--disable-dev-shm-usage')
default_chrome_options.add_argument('--disable-setuid-sandbox')

USAGE = """
python {name}
    启动PyWebIO服务器

python {name} auto
    使用无头浏览器进行自动化测试，并使用coverage检测代码覆盖率

python {name} debug
    使用带界面的浏览器自动化测试
"""


def run_test(server_func, test_func, address='http://localhost:8080?_pywebio_debug=1', chrome_options=None):
    """
    :param server_func: 启动PyWebIO服务器的函数
    :param test_func: 测试的函数。人工测试时不会被运行 (server_proc, browser)
    :param port: 启动的PyWebIO服务器的端口
    """
    if len(sys.argv) not in (1, 2) or (len(sys.argv) == 2 and sys.argv[-1] not in ('server', 'auto', 'debug')):
        print(USAGE.format(name=sys.argv[0]))
        return

    if len(sys.argv) != 2:
        try:
            server_func()
        except KeyboardInterrupt:
            pass
        sys.exit()

    if chrome_options is None:
        chrome_options = default_chrome_options

    if sys.argv[-1] == 'auto':
        default_chrome_options.add_argument('--headless')
        proc = subprocess.Popen(['coverage', 'run', '--source', 'pywebio', '--append',
                                 sys.argv[0]], stdout=sys.stdout, stderr=subprocess.STDOUT, text=True)
    elif sys.argv[-1] == 'debug':
        proc = subprocess.Popen(['python3', sys.argv[0]], stdout=sys.stdout, stderr=subprocess.STDOUT, text=True)

    browser = None
    try:
        browser = webdriver.Chrome(chrome_options=chrome_options)
        browser.set_window_size(1000, 900)
        port_str = urlparse(address).netloc.split(':', 1)[-1] or '80'
        asyncio.run(wait_host_port('localhost', int(port_str)))
        browser.get(address)
        browser.implicitly_wait(10)
        test_func(proc, browser)
    finally:
        if browser:
            if sys.argv[-1] == 'debug':
                input('press ENTER to exit')

            browser.quit()

        # 不要使用 proc.terminate() ，因为coverage会无法保存分析数据
        proc.send_signal(signal.SIGINT)
        print("Closed browser and PyWebIO server")

