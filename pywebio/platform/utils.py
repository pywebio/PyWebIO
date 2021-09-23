import fnmatch
import json
import urllib.parse
from collections import defaultdict
from collections import namedtuple
from collections.abc import Mapping, Sequence
from functools import partial
from os import path, environ

from tornado import template

from ..__version__ import __version__ as version
from ..exceptions import PyWebIOWarning
from ..utils import isgeneratorfunction, iscoroutinefunction, get_function_name, get_function_doc, \
    get_function_attr

"""
The maximum size in bytes of a http request body or a websocket message, after which the request or websocket is aborted
Set by `start_server()` or `path_deploy()` 
Used in `file_upload()` as the `max_size`/`max_total_size` parameter default or to validate the parameter. 
"""
MAX_PAYLOAD_SIZE = 0

DEFAULT_CDN = "https://cdn.jsdelivr.net/gh/wang0618/PyWebIO-assets@v{version}/"

BOOTSTRAP_VERSION = '4.4.1'

_global_config = {'title': 'PyWebIO Application'}
config_keys = ['title', 'description', 'js_file', 'js_code', 'css_style', 'css_file']
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
        cdn = DEFAULT_CDN.format(version=version)
    elif not cdn:
        cdn = ''
    else:  # user custom cdn
        cdn = cdn.rstrip('/') + '/'

    bootstrap_css = bootstrap_css_url()

    return _index_page_tpl.generate(title=meta.title, description=meta.description, protocol=protocol,
                                    script=True, content='', base_url=cdn, bootstrap_css=bootstrap_css,
                                    js_file=meta.js_file or [], js_code=meta.js_code, css_style=meta.css_style,
                                    css_file=meta.css_file or [])


def bootstrap_css_url():
    """Get bootstrap theme css url from environment variable PYWEBIO_THEME

    PYWEBIO_THEME can be one of bootswatch themes, or a custom css url. 
    """
    theme_name = environ.get('PYWEBIO_THEME')
    bootswatch_themes = {'flatly', 'yeti', 'cerulean', 'pulse', 'journal', 'cosmo', 'sandstone', 'simplex', 'minty',
                         'slate', 'superhero', 'lumen', 'spacelab', 'materia', 'litera', 'sketchy', 'cyborg', 'solar',
                         'lux', 'united', 'darkly'}

    if theme_name in bootswatch_themes:
        return 'https://cdn.jsdelivr.net/npm/bootswatch@{version}/dist/{theme}/bootstrap.min.css'.format(
            version=BOOTSTRAP_VERSION, theme=theme_name)

    return theme_name  # it's a url


def cdn_validation(cdn, level='warn', stacklevel=3):
    """CDN availability check

    :param bool/str cdn: cdn parameter
    :param level: warn or error
    """
    assert level in ('warn', 'error')

    if cdn is True and 'dev' in version:
        if level == 'warn':
            import warnings
            warnings.warn("Default CDN is not supported in dev version. Ignore the CDN setting", PyWebIOWarning,
                          stacklevel=stacklevel)
            return False
        else:
            raise ValueError("Default CDN is not supported in dev version. Please host static files by yourself.")

    return cdn


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

    # covert dict key to str
    applications = {str(k): v for k, v in applications.items()}

    for app in applications.values():
        assert iscoroutinefunction(app) or isgeneratorfunction(app) or callable(app), \
            "Don't support application type:%s" % type(app)

    if 'index' not in applications:
        applications['index'] = _generate_default_index_app(applications)

    return applications


class OriginChecker:

    @classmethod
    def check_origin(cls, origin, allowed_origins, host):
        if cls.is_same_site(origin, host):
            return True

        return any(
            fnmatch.fnmatch(origin, patten)
            for patten in allowed_origins
        )

    @staticmethod
    def is_same_site(origin, host):
        """判断 origin 和 host 是否一致。origin 和 host 都为http协议请求头"""
        parsed_origin = urllib.parse.urlparse(origin)
        origin = parsed_origin.netloc
        origin = origin.lower()

        # Check to see that origin matches host directly, including ports
        return origin == host


def deserialize_binary_event(data: bytes):
    """
    Data format:
    | event | file_header | file_data | file_header | file_data | ...

    The 8 bytes at the beginning of each segment indicate the number of bytes remaining in the segment.

    event: {
        event: "from_submit",
        task_id: that.task_id,
        data: {
            input_name => input_data
        }
    }

    file_header: {
        'filename': file name,
        'size': file size,
        'mime_type': file type,
        'last_modified': last_modified timestamp,
        'input_name': name of input field
    }

    Example:
        b'\x00\x00\x00\x00\x00\x00\x00E{"event":"from_submit","task_id":"main-4788341456","data":{"data":1}}\x00\x00\x00\x00\x00\x00\x00Y{"filename":"hello.txt","size":2,"mime_type":"text/plain","last_modified":1617119937.276}\x00\x00\x00\x00\x00\x00\x00\x02ss'
    """
    parts = []
    start_idx = 0
    while start_idx < len(data):
        size = int.from_bytes(data[start_idx:start_idx + 8], "big")
        start_idx += 8
        content = data[start_idx:start_idx + size]
        parts.append(content)
        start_idx += size

    event = json.loads(parts[0])
    files = defaultdict(list)
    for idx in range(1, len(parts), 2):
        f = json.loads(parts[idx])
        f['content'] = parts[idx + 1]
        input_name = f.pop('input_name')
        files[input_name].append(f)

    for input_name in list(event['data'].keys()):
        if input_name in files:
            event['data'][input_name] = files[input_name]

    return event


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


def config(*, title=None, description=None, js_code=None, js_file=[], css_style=None, css_file=[]):
    """PyWebIO application configuration

    :param str title: Application title
    :param str description: Application description
    :param str js_code: The javascript code that you want to inject to page.
    :param str/list js_file: The javascript files that inject to page, can be a URL in str or a list of it.
    :param str css_style: The CSS style that you want to inject to page.
    :param str/list css_file: The CSS files that inject to page, can be a URL in str or a list of it.

    ``config()`` can be used in 2 ways: direct call and decorator.
    If you call ``config()`` directly, the configuration will be global.
    If you use ``config()`` as decorator, the configuration will only work on single PyWebIO application function.
    ::

        config(title="My application")

        @config(css_style="* { color:red }")
        def app():
            put_text("hello PyWebIO")

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
