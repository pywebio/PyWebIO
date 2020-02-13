from tornado import gen
from tornado.ioloop import IOLoop
from tornado import websocket
import json

from wsrepl.ioloop import start_ioloop
from wsrepl.interact import *
from tornado.gen import sleep

import asyncio

chat_msgs = []  # 聊天记录 (name, msg)


async def refresh_msg(my_name):
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # 仅刷新其他人的新信息
                text_print('%s:%s' % m)
        last_idx = len(chat_msgs)


# 业务逻辑 协程
@asyncio.coroutine
def main():
    """
    有返回值的交互函数需要yield from
    :return:
    """
    set_title("Chat Room")
    text_print("欢迎来到聊天室，你可以和当前所有在线的人聊天")
    nickname = yield from input("请输入你的昵称", required=True)

    chat_msgs.append(('*系统*', '%s加入房间' % nickname))
    text_print("*系统*: %s加入房间" % nickname)
    run_async(refresh_msg(nickname))

    while True:
        data = yield from input_group('输入消息', [
            input('', name='msg'),
            actions('', name='cmd', buttons=['发送', '退出'])
        ])
        if data['cmd'] == '退出':
            break

        text_print('%s:%s' % (nickname, data['msg']))
        chat_msgs.append((nickname, data['msg']))

    text_print("你已经退出聊天室")


start_ioloop(main)
