"""
聊天室
^^^^^^^^^^^
和当前所有在线的人聊天

`Demo地址 <https://pywebio.herokuapp.com/?pywebio_api=chat_room>`_  `源码 <https://github.com/wang0618/PyWebIO/blob/master/demos/chat_room.py>`_

* 使用基于协程的会话
* 使用 `run_async() <pywebio.session.run_async>` 启动后台协程
"""
from pywebio.input import *
from pywebio.output import *
from pywebio import start_server, run_async

import asyncio

chat_msgs = []  # 聊天记录 (name, msg)
online_cnt = 0  # 在线人数


async def refresh_msg(my_name):
    """刷新聊天消息"""
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # 仅刷新其他人的新信息
                put_markdown('`%s`: %s' % m)
        last_idx = len(chat_msgs)


async def main():
    global online_cnt

    set_output_fixed_height(True)
    set_title("PyWebIO Chat Room")

    put_text("欢迎来到聊天室，你可以和当前所有在线的人聊天")
    nickname = await input("请输入你的昵称", required=True, valid_func=lambda n: '无法使用该昵称' if n == '📢' else None)

    online_cnt += 1
    chat_msgs.append(('📢', '`%s`加入聊天室. 当前在线人数 %s' % (nickname, online_cnt)))
    put_markdown('`📢`: `%s`加入聊天室. 当前在线人数 %s' % (nickname, online_cnt))

    refresh_task = run_async(refresh_msg(nickname))

    while True:
        data = await input_group('发送消息', [
            input(name='msg', help_text='消息内容支持Markdown 语法'),
            actions(name='cmd', buttons=['发送', '退出'])
        ])
        if data['cmd'] == '退出':
            break

        put_markdown('`%s`: %s' % (nickname, data['msg']))
        chat_msgs.append((nickname, data['msg']))

    online_cnt -= 1
    refresh_task.close()
    chat_msgs.append(('📢', '`%s`退出聊天室. 当前在线人数 %s' % (nickname, online_cnt)))
    put_text("你已经退出聊天室")


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
