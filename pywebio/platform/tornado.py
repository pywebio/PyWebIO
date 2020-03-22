import json

import asyncio
import tornado
import tornado.websocket
from ..session import AsyncBasedSession, ThreadBasedWebIOSession, get_session_implement


def webio_handler(task_func, debug=True):
    class WSHandler(tornado.websocket.WebSocketHandler):

        def check_origin(self, origin):
            return True

        def get_compression_options(self):
            # Non-None enables compression with default options.
            return {}

        def send_msg_to_client(self, controller: AsyncBasedSession):
            for msg in controller.get_task_messages():
                self.write_message(json.dumps(msg))

        def open(self):
            print("WebSocket opened")
            self.set_nodelay(True)

            self._close_from_session = False  # 是否从session中关闭连接

            if get_session_implement() is AsyncBasedSession:
                self.controller = AsyncBasedSession(task_func, on_task_message=self.send_msg_to_client,
                                                    on_session_close=self.close)
            else:
                self.controller = ThreadBasedWebIOSession(task_func, on_task_message=self.send_msg_to_client,
                                                          on_session_close=self.close_from_session,
                                                          loop=asyncio.get_event_loop())
                print('open return, ThreadBasedWebIOSession.thread2session', ThreadBasedWebIOSession.thread2session)

        def on_message(self, message):
            # print('on_message', message)
            data = json.loads(message)
            self.controller.send_client_event(data)

        def close_from_session(self):
            self._close_from_session = True
            self.close()

        def on_close(self):
            if not self._close_from_session:
                self.controller.close(no_session_close_callback=True)
            print("WebSocket closed")

    return WSHandler
