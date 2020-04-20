import subprocess
import sys, os, signal

from selenium import webdriver
from pywebio.utils import wait_host_port
import asyncio

default_chrome_options = webdriver.ChromeOptions()
default_chrome_options.add_argument('--no-sandbox')
default_chrome_options.add_argument('--disable-extensions')
default_chrome_options.add_argument('--disable-dev-shm-usage')
default_chrome_options.add_argument('--disable-setuid-sandbox')

USAGE = """
python {name}
    启动PyWebIO服务器

python {name} auto
    使用无头浏览器自动化测试

python {name} debug
    使用带界面的浏览器自动化测试
"""


def run_test(server_func, test_func, port=8080, chrome_options=None):
    """
    :param server_func: 启动PyWebIO服务器的函数
    :param test_func: 测试的函数。人工测试时不会被运行 (server_proc, browser)
    :param port: 启动的PyWebIO服务器的端口
    """
    if len(sys.argv) not in (1, 2) or (len(sys.argv) == 2 and sys.argv[-1] not in ('server', 'auto', 'debug')):
        print(USAGE.format(name=sys.argv[0]))
        return

    if len(sys.argv) != 2:
        server_func()
        sys.exit()

    if chrome_options is None:
        chrome_options = default_chrome_options

    if sys.argv[-1] == 'auto':
        default_chrome_options.add_argument('--headless')

    if sys.argv[-1] in ('auto', 'debug'):
        proc = subprocess.Popen(['coverage', 'run', '--source', 'pywebio',
                                 sys.argv[0]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        browser = None
        try:
            browser = webdriver.Chrome(chrome_options=chrome_options)
            asyncio.run(wait_host_port('localhost', port))
            browser.get('http://localhost:%s' % port)
            browser.implicitly_wait(10)
            test_func(proc, browser)
        finally:
            if browser:
                browser.quit()

            # 不要使用 proc.terminate() ，因为coverage会无法保存分析数据
            proc.send_signal(signal.SIGINT)
            print("Closed browser and PyWebIO server")
    else:
        print(USAGE.format(name=sys.argv[0]))
