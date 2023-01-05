"""
Run the example code in the documentation online
"""
import base64

from functools import partial
from os import path, listdir
from pywebio import start_server
from pywebio.platform import config
from pywebio.session import local as session_local, info as session_info
import pywebio_battery

##########################################
# Pre-import modules for demo
import time  # lgtm [py/unused-import]
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from pywebio.pin import *
from pywebio_battery import *

##########################################

here_dir = path.dirname(path.abspath(__file__))
playground_host = "https://play.pywebio.online"


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in session_info.user_language else eng


def playground(code):
    pre_import = PRE_IMPORT
    battery_apis = pywebio_battery.__all__
    if 'pywebio_battery import' not in code and any(api in code for api in battery_apis):
        pre_import += 'from pywebio_battery import *\n'

    code = f"{pre_import}\n{code}"
    encode = base64.b64encode(code.encode('utf8')).decode('utf8')
    url = f"{playground_host}/#{encode}"
    run_js('window.open(url)', url=url)


def gen_snippets(code):
    code = code.replace('# ..demo-only', '')
    code = '\n'.join(i for i in code.splitlines() if '# ..doc-only' not in i)

    parts = code.split('\n## ----\n')
    for p in parts:
        yield p.strip('\n')


def run_code(code, scope):
    with use_scope(scope):
        try:
            """
            Remember that at module level, globals and locals are the same dictionary. 
            If exec gets two separate objects as globals and locals, 
            the code will be executed as if it were embedded in a class definition.
            https://docs.python.org/3/library/functions.html#exec
            """
            exec(code, session_local.globals)
        except Exception as e:
            toast('Exception occurred: "%s:%s"' % (type(e).__name__, e), color='error')


PRE_IMPORT = """from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from pywebio.pin import *
from pywebio import start_server
"""

APP_TPL = f"""{PRE_IMPORT}
def main():
    %s

start_server(main, port=8080, debug=True)
"""

CLIPBOARD_SETUP = """
window.writeText = function(text) {
    const input = document.createElement('textarea');
    input.style.opacity  = 0;
    input.style.position = 'absolute';
    input.style.left = '-100000px';
    document.body.appendChild(input);

    input.value = text;
    input.select();
    input.setSelectionRange(0, text.length);
    document.execCommand('copy');
    document.body.removeChild(input);
    return true;
}
"""


def copytoclipboard(code):
    code = APP_TPL % code.replace('\n', '\n    ')
    run_js("writeText(text)", text=code)
    toast('The code has been copied to the clipboard')


def handle_code(code, title):
    run_js(CLIPBOARD_SETUP)
    session_local.globals = dict(globals())
    if title:
        put_markdown('## %s' % title)

    for p in gen_snippets(code):
        with use_scope() as scope:
            put_code(p, 'python')

            put_buttons(
                [t('Run', '运行'),
                 t("Edit", '编辑'),
                 t("Copy to clipboard", '复制代码')],
                onclick=[
                    partial(run_code, code=p, scope=scope),
                    partial(playground, code=p),
                    partial(copytoclipboard, code=p)
                ]
            )

        put_markdown('----')


def get_app():
    """PyWebIO demos from document

    Run the demos from the document online.
    """
    app = {}
    try:
        demos = listdir(path.join(here_dir, 'doc_demos'))
    except Exception:
        demos = []

    for name in demos:
        code = open(path.join(here_dir, 'doc_demos', name)).read()
        title, code = code.split('\n\n', 1)
        app[name] = partial(handle_code, code=code, title=title)
        app[name] = config(title=name, description=title)(app[name])

    return app


main = get_app()
if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
