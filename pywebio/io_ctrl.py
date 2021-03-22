"""
输入输出的底层实现函数
"""
import inspect
import json
import logging
from collections import UserList
from functools import partial, wraps

from .session import chose_impl, next_client_event, get_current_task_id, get_current_session
from .utils import random_str

logger = logging.getLogger(__name__)


class Output:
    """ ``put_xxx()`` 类函数的返回值

    若 ``put_xxx()`` 调用的返回值没有被变量接收，则直接将消息发送到会话；
    否则消息则作为其他消息的一部分
    """

    @staticmethod
    def json_encoder(obj, ignore_error=False):
        """json序列化与输出相关消息的Encoder函数 """
        if isinstance(obj, Output):
            return obj.embed_data()
        elif isinstance(obj, OutputList):
            return obj.data

        if not ignore_error:
            raise TypeError('Object of type  %s is not JSON serializable' % obj.__class__.__name__)

    @classmethod
    def dump_dict(cls, data):
        # todo 使用其他方式来转换spec
        return json.loads(json.dumps(data, default=cls.json_encoder))

    @classmethod
    def safely_destruct(cls, obj):
        """安全销毁 OutputReturn 对象/包含OutputReturn对象的dict/list, 使 OutputReturn.__del__ 不进行任何操作"""
        try:
            json.dumps(obj, default=partial(cls.json_encoder, ignore_error=True))
        except Exception:
            pass

    def __init__(self, spec, on_embed=None):
        self.processed = False
        self.on_embed = on_embed or (lambda d: d)
        try:
            self.spec = type(self).dump_dict(spec)  # this may raise TypeError
        except TypeError:
            self.processed = True
            type(self).safely_destruct(spec)
            raise

        # For Context manager
        self.enabled_context_manager = False
        self.container_selector = None
        self.container_dom_id = None
        self.custom_enter = None
        self.custom_exit = None

    def enable_context_manager(self, container_selector=None, container_dom_id=None, custom_enter=None,
                               custom_exit=None):
        self.enabled_context_manager = True
        self.container_selector = container_selector
        self.container_dom_id = container_dom_id
        self.custom_enter = custom_enter
        self.custom_exit = custom_exit
        return self

    def __enter__(self):
        if not self.enabled_context_manager:
            raise RuntimeError("This output function can't be used as context manager!")
        r = self.custom_enter(self) if self.custom_enter else None
        if r is not None:
            return r
        self.container_dom_id = self.container_dom_id or random_str(10)
        self.spec['container_selector'] = self.container_selector
        self.spec['container_dom_id'] = self.container_dom_id
        self.send()
        get_current_session().push_scope(self.container_dom_id)
        return self.container_dom_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        If this method returns True,
        it means that the context manager can handle the exception,
        so that the with statement terminates the propagation of the exception
        """
        r = self.custom_exit(self, exc_type=exc_type, exc_val=exc_val, exc_tb=exc_tb) if self.custom_exit else None
        if r is not None:
            return r
        get_current_session().pop_scope()
        return False  # Propagate Exception

    def embed_data(self):
        """返回供嵌入到其他消息中的数据，可以设置一些默认值"""
        self.processed = True
        return self.on_embed(self.spec)

    def send(self):
        """发送输出内容到Client"""
        self.processed = True
        send_msg('output', self.spec)

    def __del__(self):
        """返回值没有被变量接收时的操作：直接输出消息"""
        if not self.processed:
            self.send()


class OutputList(UserList):
    """
    用于 style 对输出列表设置样式时的返回值
    """

    def __del__(self):
        """返回值没有被变量接收时的操作：顺序输出其持有的内容"""
        for o in self.data:
            o.__del__()


def safely_destruct_output_when_exp(content_param):
    """装饰器生成: 异常时安全释放 Output 对象

    :param content_param: 含有Output实例的参数名或参数名列表
    :type content_param: list/str
    :return: 装饰器
    """

    def decorator(func):
        sig = inspect.signature(func)

        @wraps(func)
        def inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                # 发生异常，安全地释放 Output 对象
                params = [content_param] if isinstance(content_param, str) else content_param
                bound = sig.bind(*args, **kwargs).arguments
                for param in params:
                    if bound.get(param):
                        Output.safely_destruct(bound.get(param))

                raise

        return inner

    return decorator


def send_msg(cmd, spec=None):
    msg = dict(command=cmd, spec=spec, task_id=get_current_task_id())
    get_current_session().send_task_command(msg)


@chose_impl
def single_input(item_spec, valid_func, preprocess_func):
    """
    Note: 鲁棒性在上层完成
    将单个input构造成input_group，并获取返回值
    :param item_spec: 单个输入项的参数 'name' must in item_spec， 参数一定已经验证通过
    :param valid_func: Not None
    :param preprocess_func: Not None, 预处理函数，在收到用户提交的单项输入的原始数据后用于在校验前对数据进行预处理
    """
    if item_spec.get('name') is None:  # single input
        item_spec['name'] = 'data'
    else:  # as input_group item
        return dict(item_spec=item_spec, valid_func=valid_func, preprocess_func=preprocess_func)

    label = item_spec['label']
    name = item_spec['name']
    # todo 是否可以原地修改spec
    item_spec['label'] = ''

    item_spec.setdefault('auto_focus', True)  # 如果没有设置autofocus参数，则开启参数  todo CHECKBOX, RADIO 特殊处理

    spec = dict(label=label, inputs=[item_spec])
    data = yield input_control(spec, {name: preprocess_func}, {name: valid_func})
    return data[name]


@chose_impl
def input_control(spec, preprocess_funcs, item_valid_funcs, form_valid_funcs=None):
    """
    发送input命令，监听事件，验证输入项，返回结果
    :param spec:
    :param preprocess_funcs: keys 严格等于 spec中的name集合
    :param item_valid_funcs: keys 严格等于 spec中的name集合
    :param form_valid_funcs:
    :return:
    """
    send_msg('input_group', spec)

    data = yield input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs)

    send_msg('destroy_form')
    return data


def check_item(name, data, valid_func, preprocess_func):
    try:
        data = preprocess_func(data)
        error_msg = valid_func(data)
    except Exception as e:
        logger.warning('Get %r in valid_func for name:"%s"', e, name)
        from pywebio.session import info as session_info
        error_msg = '字段内容不合法' if 'zh' in session_info.user_language else 'Your input is not valid'

    if error_msg is not None:
        send_msg('update_input', dict(target_name=name, attributes={
            'valid_status': False,
            'invalid_feedback': error_msg
        }))
        return False
    else:
        send_msg('update_input', dict(target_name=name, attributes={
            'valid_status': 0,  # valid_status为0表示清空valid_status标志
        }))
    return True


@chose_impl
def input_event_handle(item_valid_funcs, form_valid_funcs, preprocess_funcs):
    """
    根据提供的校验函数处理表单事件
    :param item_valid_funcs: map(name -> valid_func)  valid_func 为 None 时，不进行验证
                        valid_func: callback(data) -> error_msg or None
    :param form_valid_funcs: callback(data) -> (name, error_msg) or None
    :param preprocess_funcs:
    :return:
    """
    while True:
        event = yield next_client_event()
        event_name, event_data = event['event'], event['data']
        if event_name == 'input_event':
            input_event = event_data['event_name']
            if input_event == 'blur':
                onblur_name = event_data['name']
                check_item(onblur_name, event_data['value'], item_valid_funcs[onblur_name],
                           preprocess_funcs[onblur_name])

        elif event_name == 'from_submit':
            all_valid = True

            # 调用输入项验证函数进行校验
            for name, valid_func in item_valid_funcs.items():
                if not check_item(name, event_data[name], valid_func, preprocess_funcs[name]):
                    all_valid = False

            if all_valid:  # todo 减少preprocess_funcs[name]调用次数
                data = {name: preprocess_funcs[name](val) for name, val in event_data.items()}
                # 调用表单验证函数进行校验
                if form_valid_funcs:
                    v_res = form_valid_funcs(data)
                    if v_res is not None:
                        all_valid = False
                        onblur_name, error_msg = v_res
                        send_msg('update_input', dict(target_name=onblur_name, attributes={
                            'valid_status': False,
                            'invalid_feedback': error_msg
                        }))

            if all_valid:
                break
        elif event_name == 'from_cancel':
            data = None
            break
        else:
            logger.warning("Unhandled Event: %s", event)

    return data


def output_register_callback(callback, **options):
    """向当前会话注册毁掉函数"""
    task_id = get_current_session().register_callback(callback, **options)
    return task_id
