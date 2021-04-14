import fnmatch
import json
import urllib.parse
from collections import defaultdict
from collections import namedtuple
from collections.abc import Mapping, Sequence
from functools import partial
from os import path

from tornado import template

from ..__version__ import __version__ as version
from ..exceptions import PyWebIOWarning
from ..utils import isgeneratorfunction, iscoroutinefunction, get_function_name, get_function_doc, \
    get_function_seo_info

"""
The maximum size in bytes of a http request body or a websocket message, after which the request or websocket is aborted
Set by `start_server()` or `path_deploy()` 
Used in `file_upload()` as the `max_size`/`max_total_size` parameter default or to validate the parameter. 
"""
MAX_PAYLOAD_SIZE = 0

DEFAULT_CDN = "https://cdn.jsdelivr.net/gh/wang0618/PyWebIO-assets@v{version}/"

AppMeta = namedtuple('App', 'title description')

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

    return _index_page_tpl.generate(title=meta.title or 'PyWebIO Application',
                                    description=meta.description, protocol=protocol,
                                    script=True, content='', base_url=cdn)


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
    """解析pywebio app元数据"""
    seo_info = get_function_seo_info(func)
    if seo_info:
        return AppMeta(*seo_info)

    doc = get_function_doc(func)
    parts = doc.strip().split('\n\n', 1)
    if len(parts) == 2:
        title, description = parts
    else:
        title, description = parts[0], ''

    return AppMeta(title, description)


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

    If not ``seo()`` is not used, the `docstring <https://www.python.org/dev/peps/pep-0257/>`_ of the task function will be regarded as SEO information by default.

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
    """

    if app is not None:
        return seo(title, description)(app)

    def decorator(func):
        try:
            func = partial(func)
            func._pywebio_title = title
            func._pywebio_description = description or ''
        except Exception:
            pass
        return func

    return decorator
