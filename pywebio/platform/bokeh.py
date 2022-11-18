import asyncio
import re
from collections.abc import Sequence

from pywebio.output import *
from pywebio.session import get_info

requirejs_config_tpl = """
<script type="text/javascript">
require.config({
    paths: {
        "bokeh": "https://cdn.bokeh.org/bokeh/release/bokeh-__version__.min",
        "bokeh-widgets": "https://cdn.bokeh.org/bokeh/release/bokeh-widgets-__version__.min",
        "bokeh-tables": "https://cdn.bokeh.org/bokeh/release/bokeh-tables-__version__.min",
        "bokeh-api": "https://cdn.bokeh.org/bokeh/release/bokeh-api-__version__.min",
        "bokeh-gl": "https://cdn.bokeh.org/bokeh/release/bokeh-gl-__version__.min",
    },
    shim: {
        'bokeh': {
            exports: 'Bokeh'
        },
        'bokeh-widgets': {
            exports: '_',
            deps: ['bokeh'],
        },
        'bokeh-tables': {
            exports: '_',
            deps: ['bokeh'],
        },
        'bokeh-api': {
            exports: '_',
            deps: ['bokeh'],
        },
        'bokeh-gl': {
            exports: '_',
            deps: ['bokeh'],
        },
    }
});
</script>
"""

requirejs_tpl = """
%s
<script type="text/javascript">
requirejs(['bokeh', 'bokeh-widgets', 'bokeh-tables'], function(Bokeh) {
    %s
});
</script>
"""


def load_notebook(resources=None, verbose=False, hide_banner=False, load_timeout=5000):
    """加载 Bokeh 资源

    :param resources: 目前不支持自定义静态资源的链接
    :param verbose: 开启 Bokeh 日志 并显示 Bokeh 加载标签
    :param hide_banner: 不支持
    :param load_timeout: 不支持
    :return: None
    """
    from bokeh import __version__
    from bokeh.util.serialization import make_id

    js_gists = ["console.log('Load BokehJS complete.')"]

    html = requirejs_config_tpl.replace('__version__', __version__)
    if verbose:
        element_id = make_id()
        html += """
        <div class="bk-root">
            <a href="https://bokeh.org" target="_blank" class="bk-logo bk-logo-small bk-logo-notebook"></a>
            <span id="{element_id}" style="font-family: Helvetica, Arial, sans-serif;font-size: 13px;">Loading BokehJS ...</span>
        </div>
        """.format(element_id=element_id)

        js_gists.append(
            "document.getElementById({element_id}).innerHTML = 'Load BokehJS complete.'".format(element_id=element_id))

        js_gists.append('Bokeh.set_log_level("info");')
        js_gists.append("console.log('Set bokeh log level to INFO because you set `output_notebook(verbose=True)`')")

    put_html(requirejs_tpl % (html, '\n'.join(js_gists)), sanitize=False)


def show_doc(obj, state, notebook_handle):
    """Show a document of Bokeh

    :param obj:
    :param state:
    :param notebook_handle: 不支持
    :return:
    """
    from bokeh.embed import components

    script, div = components(obj, wrap_script=False)
    if isinstance(obj, Sequence):
        div = '\n'.join(div)
    elif isinstance(obj, dict):
        div = '\n'.join(div[k] for k in obj.keys())

    put_html(requirejs_tpl % (div, script), sanitize=False)


def show_app(app, state, notebook_url, port=0, **kw):
    """Show Bokeh applications

    :param app: A Bokeh Application to embed in PyWebIO.
    :param state: ** Unused **
    :param notebook_url:  ** Unused **
    :param port: Bokeh Server 端口
    :param kw: 传给 Bokeh Server 的额外参数
    """

    from bokeh.server.server import Server
    from bokeh.io.notebook import _origin_url, uuid4, curstate, _server_url

    from pywebio.platform.tornado import ioloop
    loop = ioloop()
    if loop is None:
        toast("Currently only supports showing bokeh application in Tornado backend",
              color='error', duration=0)
        return
    loop.make_current()
    asyncio.set_event_loop(loop.asyncio_loop)
    # loop = IOLoop.current()

    info = get_info()

    allow_websocket_origin = [info.server_host]
    if info.origin:
        allow_websocket_origin.append(_origin_url(info.origin))

    server = Server({"/": app}, io_loop=loop, port=port, allow_websocket_origin=allow_websocket_origin, **kw)

    server_id = uuid4().hex
    curstate().uuid_to_server[server_id] = server

    server.start()

    url = _server_url(info.server_host, server.port)

    from bokeh.embed import server_document
    script = server_document(url, resources=None)

    script = re.sub(r'<script(.*?)>([\s\S]*?)</script>',  # lgtm [py/bad-tag-filter]
                    r"""
                    <script \g<1>>
                        requirejs(['bokeh', 'bokeh-widgets', 'bokeh-tables'], function(Bokeh) {
                            \g<2>
                        });
                    </script>
                    """, script, flags=re.I)

    put_html(script, sanitize=False)


def try_install_bokeh_hook():
    """尝试安装bokeh支持"""
    try:
        from bokeh.io import install_notebook_hook
    except ImportError:
        return False

    install_notebook_hook('pywebio', load_notebook, show_doc, show_app)
    return True
