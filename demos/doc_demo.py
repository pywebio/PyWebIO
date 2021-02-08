"""
文档中示例代码在线运行
^^^^^^^^^^^^^^^^
"""
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import *
from os import path, listdir
from functools import partial
from pywebio.platform import seo

here_dir = path.dirname(path.abspath(__file__))


def gen_snippets(code):
    code = code.replace('# ..demo-only', '')
    code = '\n'.join(i for i in code.splitlines() if '# ..doc-only' not in i)

    parts = code.split('\n## ----\n')
    for p in parts:
        yield p.strip('\n')


def run_code(code, scope, locals):
    with use_scope(scope):
        try:
            exec(code, globals(), locals)
        except Exception as e:
            toast('代码产生异常："%s:%s"' % (type(e).__name__, e), color='error')


IMPORT_CODE = """from pywebio.input import *
from pywebio.output import *
from pywebio.session import *

"""


def copytoclipboard(code):
    code = IMPORT_CODE + code
    if 'put_buttons(' in code or 'put_file(' in code:
        code += '\n\nhold()  # keep session alive'
    run_js("writeText(text)", text=code)
    toast('已复制')


def handle_code(code, title):
    run_js("""
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
    """)
    locals = {}
    if title:
        put_markdown('## %s' % title)

    for p in gen_snippets(code):
        with use_scope() as scope:
            put_code(p, 'python')

            put_buttons(['运行', '复制代码'], onclick=[
                partial(run_code, code=p, scope=scope, locals=locals),
                partial(copytoclipboard, code=p)
            ])

        put_markdown('----')

    hold()


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
        app[name] = seo('', title, app[name])

    return app


if __name__ == '__main__':
    a = get_app()
    start_server(get_app(), debug=True, port=8080, cdn=False)
