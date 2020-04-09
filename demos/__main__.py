import tornado.ioloop
import tornado.web

from demos.bmi import main as bmi
from demos.chat_room import main as chat_room
from demos.input_usage import main as input_usage
from demos.output_usage import main as output_usage

from pywebio import STATIC_PATH
from pywebio.output import put_markdown
from pywebio.platform.tornado import webio_handler
from tornado.options import define, options

index_md = r"""# PyWebIO demos
### Demos list

* [BMI计算](./?pywebio_api=bmi): 根据身高体重计算BMI指数
* [聊天室](./?pywebio_api=chat_room): 和当前所有在线的人聊天
* [输入演示](./?pywebio_api=input_usage):  演示PyWebIO输入模块的用法
* [输出演示](./?pywebio_api=output_usage): 演示PyWebIO输出模块的用法

### Links
* PyWebIO Github [github.com/wang0618/PyWebIO](https://github.com/wang0618/PyWebIO)
* 使用手册和开发文档见 [pywebio.readthedocs.io](https://pywebio.readthedocs.io)

"""


def index():
    put_markdown(index_md)


if __name__ == "__main__":
    define("port", default=5000, help="run on the given port", type=int)
    tornado.options.parse_command_line()

    application = tornado.web.Application([
        (r"/io", webio_handler(index)),
        (r"/bmi", webio_handler(bmi)),
        (r"/chat_room", webio_handler(chat_room)),
        (r"/input_usage", webio_handler(input_usage)),
        (r"/output_usage", webio_handler(output_usage)),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})
    ])
    application.listen(port=options.port)
    tornado.ioloop.IOLoop.current().start()
