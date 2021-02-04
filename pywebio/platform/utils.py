from collections import namedtuple
from collections.abc import Mapping, Sequence
from os import path

from tornado import template

from ..utils import isgeneratorfunction, iscoroutinefunction, get_function_name, get_function_doc

AppMeta = namedtuple('App', 'title description')

_here_dir = path.dirname(path.abspath(__file__))
_index_page_tpl = template.Template(open(path.join(_here_dir, 'tpl', 'index.html')).read())


def render_page(app, protocol):
    """渲染首页

    :param callable app: PyWebIO app
    :param str protocol: 'ws'/'http'
    :return: bytes
    """
    assert protocol in ('ws', 'http')
    meta = parse_app_metadata(app)
    return _index_page_tpl.generate(title=meta.title, description=meta.description, protocol=protocol)


def parse_app_metadata(func):
    """解析函数注释文档"""
    doc = get_function_doc(func)
    doc = doc.strip().split('\n\n', 1)
    if len(doc) == 1:
        title, description = doc[0] or 'PyWebIO Application', ''
    else:
        title, description = doc

    return AppMeta(title, description)


def _generate_index(applications):
    """生成默认的主页任务函数"""

    md_text = "## Application index\n"
    for name, task in applications.items():
        # todo 保留当前页面的设置项
        md_text += "- [{name}](?app={name}): {desc}\n".format(name=name, desc=get_function_doc(task))

    def index():
        from pywebio.output import put_markdown
        put_markdown(md_text)

    return index


def make_applications(applications):
    """格式化 applications 为 任务名->任务函数 的映射, 并提供默认主页

    :param applications: 接受 单一任务函数、字典、列表 类型
    :return dict: 任务名->任务函数 的映射
    """
    if isinstance(applications, Sequence):  # 列表 类型
        applications = {get_function_name(func): func for func in applications}
    elif not isinstance(applications, Mapping):  # 单一任务函数 类型
        applications = {'index': applications}

    for app in applications.values():
        assert iscoroutinefunction(app) or isgeneratorfunction(app) or callable(app), \
            "Don't support application type:%s" % type(app)

    if 'index' not in applications:
        applications['index'] = _generate_index(applications)

    return applications
