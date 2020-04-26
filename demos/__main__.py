import tornado.ioloop
import tornado.web

from demos.bmi import main as bmi
from demos.chat_room import main as chat_room
from demos.input_usage import main as input_usage
from demos.output_usage import main as output_usage
from demos.config import charts_demo_host

from pywebio import STATIC_PATH
from pywebio.output import put_markdown, set_auto_scroll_bottom
from pywebio.platform.tornado import webio_handler
from tornado.options import define, options

index_md = r"""# PyWebIO demos
### 基本demo

 - [BMI计算](./?pywebio_api=bmi): 根据身高体重计算BMI指数 [源码](https://github.com/wang0618/PyWebIO/blob/master/demos/bmi.py)
 - [聊天室](./?pywebio_api=chat_room): 和当前所有在线的人聊天 [源码](https://github.com/wang0618/PyWebIO/blob/master/demos/chat_room.py)
 - [输入演示](./?pywebio_api=input_usage):  演示PyWebIO输入模块的用法 [源码](https://github.com/wang0618/PyWebIO/blob/master/demos/input_usage.py)
 - [输出演示](./?pywebio_api=output_usage): 演示PyWebIO输出模块的用法 [源码](https://github.com/wang0618/PyWebIO/blob/master/demos/output_usage.py)

### 数据可视化demo
PyWebIO还支持使用第三方库进行数据可视化

 - 使用`pyecharts`创建基于Echarts的图表 [**demos**]({charts_demo_host}/?pywebio_api=pyecharts)
 - 使用`cutecharts.py`创建卡通风格图表 [**demos**]({charts_demo_host}/?pywebio_api=cutecharts)
 - 使用`plotly`进行数据可视化 [**demos**]({charts_demo_host}/?pywebio_api=plotly)

**数据可视化demo截图**

![pyecharts](https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/pyecharts.gif)

![cutecharts](https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/cutecharts.png)

![plotly](https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/plotly.png)

### Links
* PyWebIO Github [github.com/wang0618/PyWebIO](https://github.com/wang0618/PyWebIO)
* 使用手册和实现文档见 [pywebio.readthedocs.io](https://pywebio.readthedocs.io)

""".format(charts_demo_host=charts_demo_host)


def index():
    set_auto_scroll_bottom(False)
    put_markdown(index_md)


if __name__ == "__main__":
    define("port", default=8080, help="run on the given port", type=int)
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
