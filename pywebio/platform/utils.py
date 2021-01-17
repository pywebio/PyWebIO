from collections.abc import Mapping, Sequence
from ..utils import isgeneratorfunction, iscoroutinefunction, get_function_name
import inspect


def _generate_index(applications):
    """生成默认的主页任务函数"""

    md_text = "## Application index\n"
    for name, task in applications.items():
        # todo 保留当前页面的设置项
        md_text += "- [{name}](?app={name}): {desc}\n".format(name=name, desc=(inspect.getdoc(task) or ''))

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
