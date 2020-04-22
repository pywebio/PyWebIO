<h1 align="center">PyWebIO</h1>
<p align="center">
    <em>Write web app in script way.</em>
</p>
<p align="center">
    <a href="https://percy.io/pywebio/pywebio">
        <img src="https://percy.io/static/images/percy-badge.svg" alt="Percy visual test">
    </a>
    <a href="https://codecov.io/gh/wang0618/PyWebIO">
        <img src="https://codecov.io/gh/wang0618/PyWebIO/branch/dev/graph/badge.svg" />
    </a>
    <a href="https://pywebio.readthedocs.io/zh_CN/latest/?badge=latest">
        <img src="https://readthedocs.org/projects/pywebio/badge/?version=latest" alt="Documentation Status">
    </a>
    <a href="https://badge.fury.io/py/PyWebIO">
        <img src="https://badge.fury.io/py/PyWebIO.svg" alt="Package version">
    </a>
    <a href="https://pypi.org/project/PyWebIO/">
        <img src="https://img.shields.io/pypi/pyversions/PyWebIO.svg?colorB=brightgreen" alt="Python Version">
    </a>
    <a href="https://github.com/wang0618/PyWebIO/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/wang0618/PyWebIO" alt="License">
    </a>
</p>

PyWebIO是一个用于在浏览器上获取输入和进行输出的工具库。能够将原有的通过终端交互的脚本快速服务化，供其他人在网络上通过浏览器访问使用；
PyWebIO还可以方便地整合进现有的Web服务，让你不需要编写Html和JS代码，就可以构建出具有良好可用性的Web程序。

特点：

- 使用同步而不是基于回调的方式获取输入，无需在各个步骤之间保存状态，使用更方便
- 代码侵入性小，对于旧脚本代码仅需修改输入输出逻辑
- 支持多用户与并发请求
- 支持结合第三方库实现数据可视化
- 支持整合到现有的Web服务，目前支持与Tornado和Flask的集成
- 同时支持基于线程的执行模型和基于协程的执行模型


## Install

PyPi安装:

```bash
pip3 install -U pywebio
```

目前PyWebIO处于快速开发迭代中，PyPi上的包更新可能滞后，建议使用源码安装:

```bash
pip3 install -U https://code.aliyun.com/wang0618/pywebio/repository/archive.zip
```

**系统要求**: PyWebIO要求 Python 版本在 3.5.2 及以上

## Quick start

**Hello, world**

这是一个使用PyWebIO计算 [BMI指数](https://en.wikipedia.org/wiki/Body_mass_index>) 的脚本:

```python
from pywebio.input import input, FLOAT
from pywebio.output import put_text

def bmi():
    height = input("请输入你的身高(cm)：", type=FLOAT)
    weight = input("请输入你的体重(kg)：", type=FLOAT)

    BMI = weight / (height / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            put_text('你的 BMI 值: %.1f，身体状态：%s' % (BMI, status))
            break

if __name__ == '__main__':
    bmi()
```


如果没有使用PywWebIO，这只是一个非常简单的脚本，而通过使用PywWebIO提供的输入输出函数，你可以在浏览器中与代码进行交互：

<p align="center">
    <a href="https://pywebio.herokuapp.com/">
        <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/master/docs/assets/demo.gif" alt="PyWebIO demo"/>
    </a>
</p>

**向外提供服务**

上文对使用PyWebIO进行改造的程序，运行模式还是脚本，程序计算完毕后立刻退出。可以使用 [`pywebio.start_server()`](https://pywebio.readthedocs.io/zh_CN/latest/platform.html#pywebio.platform.start_server) 将 `bmi()` 函数作为Web服务提供：

```python
from pywebio import start_server
from pywebio.input import input, FLOAT
from pywebio.output import put_text

def bmi():
    ...  # bmi() 函数内容不变

if __name__ == '__main__':
    start_server(bmi)
```



**与现有Web框架整合**

仅需在现有的Tornado应用中加入加入两个 `RequestHandler` ，就可以将使用PyWebIO编写的函数整合进Tornado应用中

```python
import tornado.ioloop
import tornado.web
from pywebio.platform.tornado import webio_handler
from pywebio import STATIC_PATH

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/bmi/io", webio_handler(bmi)),  # bmi 即为上文计算BMI指数的函数
        (r"/bmi/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})
    ])
    application.listen(port=80, address='localhost')
    tornado.ioloop.IOLoop.current().start()
```

在 `http://localhost/bmi/` 页面上就可以计算BMI了

## Demos

 - [数据可视化demo](http://pywebio-charts.wangweimin.site/) : 使用 plotly、pyecharts 等库创建图表
 - [其他demo](https://pywebio.herokuapp.com/) : 包含PyWebIO基本输入输出演示和使用PyWebIO编写的小应用

## Document

使用手册和实现文档见 [https://pywebio.readthedocs.io](https://pywebio.readthedocs.io)

