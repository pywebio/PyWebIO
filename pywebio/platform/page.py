import urllib.parse
from collections import namedtuple
from collections.abc import Mapping, Sequence
from functools import lru_cache
from functools import partial
from os import path, environ

from tornado import template

from ..__version__ import __version__ as version
from ..utils import isgeneratorfunction, iscoroutinefunction, get_function_name, get_function_doc, \
    get_function_attr, STATIC_PATH

"""
The maximum size in bytes of a http request body or a websocket message, after which the request or websocket is aborted
Set by `start_server()` or `path_deploy()` 
Used in `file_upload()` as the `max_size`/`max_total_size` parameter default or to validate the parameter. 
"""
MAX_PAYLOAD_SIZE = 0

DEFAULT_CDN = "https://cdn.jsdelivr.net/gh/wang0618/PyWebIO-assets@v{version}/"

_global_config = {'title': 'PyWebIO Application'}
config_keys = ['title', 'description', 'js_file', 'js_code', 'css_style', 'css_file', 'theme']
AppMeta = namedtuple('App', config_keys)

_here_dir = path.dirname(path.abspath(__file__))
_index_page_tpl = template.Template(open(path.join(_here_dir, 'tpl', 'index.html'), encoding='utf8').read())


def render_page(app, protocol, cdn):
    """渲染前端页面的HTML框架, 支持SEO

    :param callable app: PyWebIO app
    :param str protocol: 'ws'/'http'
    :param bool/str cdn: Whether to use CDN, also accept string as custom CDN URL
    :return: bytes content of rendered page
    """
    assert protocol in ('ws', 'http')
    meta = parse_app_metadata(app)
    if cdn is True:
        base_url = DEFAULT_CDN.format(version=version)
    elif not cdn:
        base_url = ''
    else:  # user custom cdn
        base_url = cdn.rstrip('/') + '/'

    theme = environ.get('PYWEBIO_THEME', meta.theme) or 'default'
    check_theme(theme)

    return _index_page_tpl.generate(title=meta.title, description=meta.description, protocol=protocol,
                                    script=True, content='', base_url=base_url,
                                    js_file=meta.js_file or [], js_code=meta.js_code, css_style=meta.css_style,
                                    css_file=meta.css_file or [], theme=theme)


@lru_cache(maxsize=64)
def check_theme(theme):
    """check theme file existence"""
    if not theme:
        return

    theme_file = path.join(STATIC_PATH, 'css', 'bs-theme', theme + '.min.css')
    if not path.isfile(theme_file):
        raise RuntimeError("Can't find css file for theme `%s`" % theme)


def parse_app_metadata(func):
    """Get metadata form pywebio task function, fallback to global config in empty meta field."""
    prefix = '_pywebio_'
    attrs = get_function_attr(func, [prefix + k for k in config_keys])
    meta = AppMeta(**{k: attrs.get(prefix + k) for k in config_keys})

    doc = get_function_doc(func)
    parts = doc.strip().split('\n\n', 1)
    if len(parts) == 2:
        title, description = parts
    else:
        title, description = parts[0], ''

    if not meta.title:
        meta = meta._replace(title=title, description=description)

    # fallback to global config
    for key in config_keys:
        if not getattr(meta, key, None) and _global_config.get(key):
            kwarg = {key: _global_config.get(key)}
            meta = meta._replace(**kwarg)

    return meta


_app_list_tpl = template.Template("""
<h1>Applications index</h1>
<ul>
    {% for name,meta in apps_info.items() %}
    <li>
        {% if other_arguments is not None %}
            <a href="?app={{name}}{{other_arguments}}">{{ meta.title or name }}</a>:
        {% else %}
            <a href="javascript:WebIO.openApp('{{ name }}', true)">{{ meta.title or name }}</a>:
        {% end %}

        {% if meta.description %}
            {{ meta.description }} 
        {% else %}
            <i>No description.</i>
        {% end %}
    </li>
    {% end %}
</ul>
""".strip())


def get_static_index_content(apps, query_arguments=None):
    """生成默认的静态主页

    :param callable apps: PyWebIO apps
    :param str query_arguments: Url Query Arguments。为None时，表示使用WebIO.openApp跳转
    :return: bytes
    """
    apps_info = {
        name: parse_app_metadata(func)
        for name, func in apps.items()
    }

    qs = urllib.parse.parse_qs(query_arguments)
    qs.pop('app', None)
    other_arguments = urllib.parse.urlencode(qs, doseq=True)

    if other_arguments:
        other_arguments = '&' + other_arguments
    else:
        other_arguments = None
    content = _app_list_tpl.generate(apps_info=apps_info, other_arguments=other_arguments).decode('utf8')
    return content


def _generate_default_index_app(apps):
    """默认的主页任务函数"""
    content = get_static_index_content(apps)

    def index():
        from pywebio.output import put_html
        put_html(content)

    return index


def make_applications(applications):
    """格式化 applications 为 任务名->任务函数 的映射, 并提供默认主页

    :param applications: 接受 单一任务函数、字典、列表 类型
    :return dict: 任务名->任务函数 的映射
    """

    if isinstance(applications, Sequence):  # 列表 类型
        applications, app_list = {}, applications
        for func in app_list:
            name = get_function_name(func)
            if name in applications:
                raise ValueError("Duplicated application name:%r" % name)
            applications[name] = func
    elif not isinstance(applications, Mapping):  # 单一任务函数 类型
        applications = {'index': applications}

    # convert dict key to str
    applications = {str(k): v for k, v in applications.items()}

    for app in applications.values():
        assert iscoroutinefunction(app) or isgeneratorfunction(app) or callable(app), \
            "Don't support application type:%s" % type(app)

    if 'index' not in applications:
        applications['index'] = _generate_default_index_app(applications)

    return applications


def seo(title, description=None, app=None):
    """Set the SEO information of the PyWebIO application (web page information provided when indexed by search engines)

    :param str title: Application title
    :param str description: Application description
    :param callable app: PyWebIO task function

    If ``seo()`` is not used, the `docstring <https://www.python.org/dev/peps/pep-0257/>`_ of the task function will be regarded as SEO information by default.

    ``seo()`` can be used in 2 ways: direct call and decorator::

        @seo("title", "description")
        def foo():
            pass

        def bar():
            pass

        def hello():
            \"""Application title

            Application description...
            (A empty line is used to separate the description and title)
            \"""

        start_server([
            foo,
            hello,
            seo("title", "description", bar),
        ])

    .. versionadded:: 1.1
    .. deprecated:: 1.4
        Use :func:`pywebio.config` instead.
    """
    import warnings
    warnings.warn("`pywebio.platform.seo()` is deprecated since v1.4 and will remove in the future version, "
                  "use `pywebio.config` instead", DeprecationWarning, stacklevel=2)

    if app is not None:
        return config(title=title, description=description)(app)

    return config(title=title, description=description)


def config(*, title=None, description=None, theme=None, js_code=None, js_file=[], css_style=None, css_file=[]):
    """PyWebIO application configuration

    :param str title: Application title
    :param str description: Application description
    :param str theme: Application theme. Available themes are: ``dark``, ``sketchy``, ``minty``, ``yeti``.
        You can also use environment variable ``PYWEBIO_THEME`` to specify the theme (with high priority).

        :demo_host:`Theme preview demo </theme>`

        .. collapse:: Open Source Credits

            The dark theme is modified from ForEvolve's `bootstrap-dark <https://github.com/ForEvolve/bootstrap-dark>`_.
            The sketchy, minty and yeti theme are from `bootswatch <https://bootswatch.com/4/>`_.

    :param str js_code: The javascript code that you want to inject to page.
    :param str/list js_file: The javascript files that inject to page, can be a URL in str or a list of it.
    :param str css_style: The CSS style that you want to inject to page.
    :param str/list css_file: The CSS files that inject to page, can be a URL in str or a list of it.

    ``config()`` can be used in 2 ways: direct call and decorator.
    If you call ``config()`` directly, the configuration will be global.
    If you use ``config()`` as decorator, the configuration will only work on single PyWebIO application function.
    ::

        config(title="My application")  # global configuration

        @config(css_style="* { color:red }")  # only works on this application
        def app():
            put_text("hello PyWebIO")

    .. note:: The configuration will affect all sessions

    ``title`` and ``description`` are used for SEO, which are provided when indexed by search engines.
    If no ``title`` and ``description`` set for a PyWebIO application function,
    the `docstring <https://www.python.org/dev/peps/pep-0257/>`_ of the function will be used as title and description by default::

        def app():
            \"""Application title

            Application description...
            (A empty line is used to separate the description and title)
            \"""
            pass

    The above code is equal to::

        @config(title="Application title", description="Application description...")
        def app():
            pass

    .. versionadded:: 1.4

    .. versionchanged:: 1.5
       add ``theme`` parameter
    """
    if isinstance(js_file, str):
        js_file = [js_file]
    if isinstance(css_file, str):
        css_file = [css_file]

    configs = locals()

    class Decorator:
        def __init__(self):
            self.called = False

        def __call__(self, func):
            self.called = True
            try:
                func = partial(func)  # to make a copy of the function
                for key, val in configs.items():
                    if val:
                        setattr(func, '_pywebio_%s' % key, val)
            except Exception:
                pass
            return func

        def __del__(self):  # if not called as decorator, set the config to global
            if self.called:
                return

            global _global_config
            _global_config = configs

    return Decorator()
