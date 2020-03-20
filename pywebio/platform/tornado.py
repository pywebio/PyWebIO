import json

import tornado
import tornado.websocket
from ..session import AsyncBasedSession


def webio_handler(coro_func, debug=True):
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

            self.controller = AsyncBasedSession(coro_func, on_task_message=self.send_msg_to_client,
                                                on_session_close=self.close)

        def on_message(self, message):
            # print('on_message', message)
            data = json.loads(message)
            self.controller.send_client_event(data)

        def on_close(self):
            self.controller.close(no_session_close_callback=True)
            print("WebSocket closed")

    return WSHandler
