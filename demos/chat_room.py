"""
聊天室
^^^^^^^^^^^
和当前所有在线的人聊天

:demo_host:`Demo地址 </?pywebio_api=chat_room>`  `源码 <https://github.com/wang0618/PyWebIO/blob/master/demos/chat_room.py>`_

* 使用基于协程的会话
* 使用 `run_async() <pywebio.session.run_async>` 启动后台协程
"""
import asyncio

from pywebio import start_server, run_async
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call

# 最大消息记录保存
MAX_MESSAGES_CNT = 10 ** 4

chat_msgs = []  # 聊天记录 (name, msg)
online_users = set()  # 在线用户


async def refresh_msg(my_name):
    """刷新聊天消息"""
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # 仅刷新其他人的新信息
                put_markdown('`%s`: %s' % m)

        # 清理聊天记录
        if len(chat_msgs) > MAX_MESSAGES_CNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


async def main():
    global chat_msgs

    set_output_fixed_height(True)
    set_title("PyWebIO Chat Room")
    put_markdown("""欢迎来到聊天室，你可以和当前所有在线的人聊天\n
    本应用使用不到80行代码实现，源代码[链接](https://github.com/wang0618/PyWebIO/blob/master/demos/chat_room.py)""", lstrip=True)

    nickname = await input("请输入你的昵称", required=True,
                           valid_func=lambda n: '昵称已被使用' if n in online_users or n == '📢' else None)

    online_users.add(nickname)
    chat_msgs.append(('📢', '`%s`加入聊天室. 当前在线人数 %s' % (nickname, len(online_users))))
    put_markdown('`📢`: `%s`加入聊天室. 当前在线人数 %s' % (nickname, len(online_users)))

    @defer_call
    def on_close():
        online_users.remove(nickname)
        chat_msgs.append(('📢', '`%s`退出聊天室. 当前在线人数 %s' % (nickname, len(online_users))))

    refresh_task = run_async(refresh_msg(nickname))

    while True:
        data = await input_group('发送消息', [
            input(name='msg', help_text='消息内容支持Markdown 语法', required=True),
            actions(name='cmd', buttons=['发送', {'label': '退出', 'type': 'cancel'}])
        ])
        if data is None:
            break

        put_markdown('`%s`: %s' % (nickname, data['msg']))
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()
    put_text("你已经退出聊天室")


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
