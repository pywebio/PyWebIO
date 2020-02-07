import tornado.websocket
import time, json
from collections import defaultdict
from .framework import Future, Msg, Global


def _get_response(cmd, spec, gen_msg_id=False):
    """
    yield出来的为Future对象，每次yield前注册event，event的callback为给该Future对象set-result
    yield的返回值为改Future对象的值
    :return:
    """

    # 注册event
    msg_id = Msg.gen_msg_id()
    spec['msg_id'] = msg_id
    msg = dict(command=cmd, spec=spec)
    f = Future()
    Msg.add_callback(msg_id, f.set_result)

    Global.active_ws.write_message(json.dumps(msg))

    response_msg = yield from f
    Msg.unregister_msg(msg_id)

    return response_msg


# 非阻塞协程工具库
def text_input_coro(prompt):
    input_text = yield from _get_response("text_input", spec=dict(prompt=prompt))
    return input_text


def ctrl_coro(ctrl_info):
    msg = dict(command="ctrl", spec=ctrl_info)
    Global.active_ws.write_message(json.dumps(msg))


def text_print(text, *, ws=None):
    msg = dict(command="text_print", spec=dict(content=text))
    (ws or Global.active_ws).write_message(json.dumps(msg))
