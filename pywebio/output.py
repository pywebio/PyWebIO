import json
import logging
from collections.abc import Mapping
from base64 import b64encode
from .framework import Global, Task
from .input_ctrl import send_msg, single_input, input_control, next_event, run_async
from .output_ctl import register_callback
import asyncio
import inspect


def set_title(title):
    send_msg('output_ctl', dict(title=title))


def set_output_fixed_height(enabled=True):
    send_msg('output_ctl', dict(output_fixed_height=enabled))


def set_auto_scroll_bottom(enabled=True):
    send_msg('output_ctl', dict(auto_scroll_bottom=enabled))


_AnchorTPL = 'pywebio-anchor-%s'


def set_anchor(name):
    """
    在当前输出处标记锚点。 若已经存在name锚点，则先将旧锚点删除
    """
    inner_ancher_name = _AnchorTPL % name
    send_msg('output_ctl', dict(set_anchor=inner_ancher_name))


def clear_before(anchor):
    """清除anchor锚点之前输出的内容"""
    inner_ancher_name = _AnchorTPL % anchor
    send_msg('output_ctl', dict(clear_before=inner_ancher_name))


def clear_after(anchor):
    """清除anchor锚点之后输出的内容"""
    inner_ancher_name = _AnchorTPL % anchor
    send_msg('output_ctl', dict(clear_after=inner_ancher_name))


def clear_range(start_anchor, end_anchor):
    """
    清除start_anchor-end_ancher锚点之间输出的内容.
    若 start_anchor 或 end_ancher 不存在，则不进行任何操作
    """
    inner_start_anchor_name = 'pywebio-anchor-%s' % start_anchor
    inner_end_ancher_name = 'pywebio-anchor-%s' % end_anchor
    send_msg('output_ctl', dict(clear_range=[inner_start_anchor_name, inner_end_ancher_name]))


def scroll_to(anchor):
    """将页面滚动到anchor锚点处"""
    inner_ancher_name = 'pywebio-anchor-%s' % anchor
    send_msg('output_ctl', dict(scroll_to=inner_ancher_name))


def _put_content(type, ws=None, anchor=None, before=None, after=None, **other_spec):
    """
    向浏览器输出内容
    :param type:
    :param content:
    :param ws:
    :param before:
    :param after:
    :return:
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"

    spec = dict(type=type)
    spec.update(other_spec)
    if anchor:
        spec['anchor'] = _AnchorTPL % anchor
    if before:
        spec['before'] = _AnchorTPL % before
    elif after:
        spec['after'] = _AnchorTPL % after

    msg = dict(command="output", spec=spec)
    (ws or Global.active_ws).write_message(json.dumps(msg))


def put_text(text, inline=False, ws=None, anchor=None, before=None, after=None):
    """
    输出文本内容
    :param text:
    :param ws:
    :param before:
    :param after:
    :return:
    """
    _put_content('text', content=text, inline=inline, ws=ws, anchor=anchor, before=before, after=after)


def put_html(html, anchor=None, before=None, after=None):
    _put_content('html', content=html, anchor=anchor, before=before, after=after)


def put_code(content, langage='', anchor=None, before=None, after=None):
    code = "```%s\n%s\n```" % (langage, content)
    put_markdown(code, anchor=anchor, before=before, after=after)


def put_markdown(mdcontent, strip_indent=0, lstrip=False, anchor=None, before=None, after=None):
    """
    输出Markdown内容。当在函数中使用Python的三引号语法输出多行内容时，为了排版美观可能会对Markdown文本进行缩进，
        这时候，可以设置strip_indent或lstrip来防止Markdown错误解析
    :param mdcontent: Markdown文本
    :param strip_indent: 去除行开始的缩进空白数。
    :param lstrip: 是否去除行开始的空白。
    :return:
    """
    if strip_indent:
        lines = (
            i[strip_indent:] if (i[:strip_indent] == ' ' * strip_indent) else i
            for i in mdcontent.splitlines()
        )
        mdcontent = '\n'.join(lines)
    if lstrip:
        lines = (i.lstrip() for i in mdcontent.splitlines())
        mdcontent = '\n'.join(lines)

    _put_content('markdown', content=mdcontent, anchor=anchor, before=before, after=after)


def put_table(tdata, header=None, anchor=None, before=None, after=None):
    """
    输出表格
    :param tdata: list of list|dict
    :param header: 列表，当tdata为字典列表时，header指定表头顺序
    :return:
    """
    if header:
        tdata = [
            [row.get(k, '') for k in header]
            for row in tdata
        ]

    def quote(data):
        return str(data).replace('|', r'\|')

    # 防止当tdata只有一行时，无法显示表格
    if len(tdata) == 1:
        tdata[0:0] = [' '] * len(tdata[0])

    header = "|%s|" % "|".join(map(quote, tdata[0]))
    res = [header]
    res.append("|%s|" % "|".join(['----'] * len(tdata[0])))
    for tr in tdata[1:]:
        t = "|%s|" % "|".join(map(quote, tr))
        res.append(t)
    put_markdown('\n'.join(res), anchor=anchor, before=before, after=after)


def _format_button(buttons):
    """
    格式化按钮参数
    :param buttons: button列表， button可用形式：
        {value:, label:, }
        (value, label,)
        value 单值，label等于value

    :return: [{value:, label:, }, ...]
    """

    btns = []
    for btn in buttons:
        if isinstance(btn, Mapping):
            assert 'value' in btn and 'label' in btn, 'actions item must have value and label key'
        elif isinstance(btn, list):
            assert len(btn) == 2, 'actions item format error'
            btn = dict(zip(('value', 'label'), btn))
        else:
            btn = dict(value=btn, label=btn)
        btns.append(btn)
    return btns


def td_buttons(buttons, onclick, save=None, mutex_mode=False):
    """
    在表格中显示一组按钮
    参数含义同 buttons 函数
    :return:
    """
    btns = _format_button(buttons)
    callback_id = register_callback(onclick, save, mutex_mode)
    tpl = '<button type="button" value="{value}" class="btn btn-primary btn-sm" ' \
          'onclick="WebIO.DisplayAreaButtonOnClick(this, \'%s\')">{label}</button>' % callback_id
    btns_html = [tpl.format(**b) for b in btns]
    return ' '.join(btns_html)


def put_buttons(buttons, onclick, small=False, save=None, mutex_mode=False, anchor=None, before=None, after=None):
    """
    显示一组按钮
    :param buttons: button列表， button可用形式： value 只能为字符串
        {value:, label:, }
        (value, label,)
        value 单值，label等于value
    :param onclick: CallBack(btn_value, save) CallBack can be generator function or coroutine function
    :param save:
    :param mutex_mode: 互斥模式，回调在运行过程中，无法响应同一回调，仅当onclick为协程函数时有效
    :return:
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"
    btns = _format_button(buttons)
    callback_id = register_callback(onclick, save, mutex_mode)
    _put_content('buttons', callback_id=callback_id, buttons=btns, small=small, anchor=anchor, before=before,
                 after=after)


def put_file(name, content, anchor=None, before=None, after=None):
    """
    :param name: file name
    :param content: bytes-like object
    :return:
    """
    assert not (before and after), "Parameter 'before' and 'after' cannot be specified at the same time"
    content = b64encode(content).decode('ascii')
    _put_content('file', name=name, content=content, anchor=anchor, before=before, after=after)
