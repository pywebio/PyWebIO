<h1 align="center" name="pywebio-en">PyWebIO</h1>
<p align="center">
    <em>Write interactive web app in script way.</em>
</p>
<p align="center">
    <a href="https://percy.io/pywebio/pywebio">
        <img src="https://percy.io/static/images/percy-badge.svg" alt="Percy visual test">
    </a>
    <a href="https://codecov.io/gh/wang0618/PyWebIO">
        <img src="https://codecov.io/gh/wang0618/PyWebIO/branch/dev/graph/badge.svg" alt="Code coverage"/>
    </a>
    <a href="https://pywebio.readthedocs.io/zh_CN/latest/?badge=latest">
        <img src="https://readthedocs.org/projects/pywebio/badge/?version=latest" alt="Documentation Status">
    </a>
    <a href="https://pypi.org/project/PyWebIO/">
        <img src="https://img.shields.io/pypi/v/pywebio?colorB=brightgreen" alt="Package version">
    </a>
    <a href="https://pypi.org/project/PyWebIO/">
        <img src="https://img.shields.io/pypi/pyversions/PyWebIO.svg?colorB=brightgreen" alt="Python Version">
    </a>
    <br/>
    <a href="https://lgtm.com/projects/g/wang0618/PyWebIO/context:python">
        <img src="https://img.shields.io/lgtm/grade/python/github/wang0618/PyWebIO.svg?colorB=brightgreen" alt="Python code quality">
    </a>
    <a href="https://lgtm.com/projects/g/wang0618/PyWebIO/context:javascript">
        <img src="https://img.shields.io/lgtm/grade/javascript/github/wang0618/PyWebIO.svg?colorB=brightgreen" alt="Javascript code quality">
    </a>
    <a href="https://github.com/wang0618/PyWebIO/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/wang0618/PyWebIO.svg" alt="License">
    </a>
    <br/>
    <a href="https://pywebio.readthedocs.io">[Document]</a> | <a href="http://pywebio-demos.demo.wangweimin.site/">[Demos]</a> | <a href="https://github.com/wang0618/PyWebIO/wiki/Why-PyWebIO%3F">[Why PyWebIO?]</a>
</p>

[English](#pywebio-en) | [中文](#pywebio-zh)

PyWebIO provides a series of imperative functions to obtain user input and output on the browser, turning the browser into a "rich text terminal", and can be used to build simple web applications or browser-based GUI applications without the need to have knowledge of HTML and JS. PyWebIO can also be easily integrated into existing Web services. PyWebIO is very suitable for quickly building applications that do not require complex UI.

<p align="center">
    <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/output_demo.gif" alt="PyWebIO output demo" width='609px'/>
    <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/input_demo.gif" alt="PyWebIO input demo" width='609px'/>
</p>


Features：

- Use synchronization instead of callback-based method to get input
- Non-declarative layout, simple and efficient
- Less intrusive: old script code can be transformed into a Web application only by modifying the input and output operation
- Support integration into existing web services, currently supports Flask, Django, Tornado, aiohttp framework
- Support for ``asyncio`` and coroutine
- Support data visualization with third-party libraries, e.g., `plotly`, `bokeh`, `pyecharts`.

## Installation

Stable version:

```bash
pip3 install -U pywebio
```

Development version:
```bash
pip3 install -U https://code.aliyun.com/wang0618/pywebio/repository/archive.zip
```

**Prerequisites**: PyWebIO requires Python 3.5.2 or newer

## Quick start

**Hello, world**

Here is a simple PyWebIO script to calculate the [BMI](https://en.wikipedia.org/wiki/Body_mass_index):

```python
from pywebio.input import input, FLOAT
from pywebio.output import put_text

def bmi():
    height = input("Your Height(cm)：", type=FLOAT)
    weight = input("Your Weight(kg)：", type=FLOAT)

    BMI = weight / (height / 100) ** 2

    top_status = [(14.9, 'Severely underweight'), (18.4, 'Underweight'),
                  (22.9, 'Normal'), (27.5, 'Overweight'),
                  (40.0, 'Moderately obese'), (float('inf'), 'Severely obese')]

    for top, status in top_status:
        if BMI <= top:
            put_text('Your BMI: %.1f, category: %s' % (BMI, status))
            break

if __name__ == '__main__':
    bmi()
```

This is just a very simple script if you ignore PyWebIO, but using the input and output functions provided by PyWebIO, you can interact with the code in the browser [[demo]](http://pywebio-demos.demo.wangweimin.site/bmi):

<p align="center">
    <a href="http://pywebio-demos.demo.wangweimin.site/?pywebio_api=bmi">
        <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/demo.gif" alt="PyWebIO demo" width="400px"/>
    </a>
</p>

**Serve as web service**

The above BMI program will exit immediately after the calculation, you can use [`pywebio.start_server()`](https://pywebio.readthedocs.io/zh_CN/latest/platform.html#pywebio.platform.tornado.start_server) to publish the `bmi()` function as a web application:

```python
from pywebio import start_server
from pywebio.input import input, FLOAT
from pywebio.output import put_text

def bmi(): # bmi() keep the same
    ...  

if __name__ == '__main__':
    start_server(bmi, port=80)
```

**Integration with web framework**

To integrate PyWebIO application into Tornado, all you need is adding a `RequestHandler` to the existing Tornado application:

```python
import tornado.ioloop
import tornado.web
from pywebio.platform.tornado import webio_handler

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/bmi", webio_handler(bmi)),  # bmi is the same function as above
    ])
    application.listen(port=80, address='localhost')
    tornado.ioloop.IOLoop.current().start()
```

Now, you can open `http://localhost/bmi` for BMI calculation.

For integration with other web frameworks, please refer to [document](https://pywebio.readthedocs.io/en/latest/guide.html#integration-with-web-framework).

## Demos

 - [Basic demo](http://pywebio-demos.demo.wangweimin.site/) : PyWebIO basic input and output demos and some small applications written using PyWebIO.
 - [Data visualization demo](http://pywebio-charts.demo.wangweimin.site/) : Data visualization with the third-party libraries, e.g., `plotly`, `bokeh`, `pyecharts`.

## Document

Document is on [https://pywebio.readthedocs.io](https://pywebio.readthedocs.io)

<hr/>
<h1 align="center" name="pywebio-zh">PyWebIO</h1>
<p align="center">
    <em>Write interactive web app in script way.</em>
</p>
<p align="center">
    <a href="https://percy.io/pywebio/pywebio">
        <img src="https://percy.io/static/images/percy-badge.svg" alt="Percy visual test">
    </a>
    <a href="https://codecov.io/gh/wang0618/PyWebIO">
        <img src="https://codecov.io/gh/wang0618/PyWebIO/branch/dev/graph/badge.svg" alt="Code coverage"/>
    </a>
    <a href="https://pywebio.readthedocs.io/zh_CN/latest/?badge=latest">
        <img src="https://readthedocs.org/projects/pywebio/badge/?version=latest" alt="Documentation Status">
    </a>
    <a href="https://pypi.org/project/PyWebIO/">
        <img src="https://img.shields.io/pypi/v/pywebio?colorB=brightgreen" alt="Package version">
    </a>
    <a href="https://pypi.org/project/PyWebIO/">
        <img src="https://img.shields.io/pypi/pyversions/PyWebIO.svg?colorB=brightgreen" alt="Python Version">
    </a>
    <br/>
    <a href="https://lgtm.com/projects/g/wang0618/PyWebIO/context:python">
        <img src="https://img.shields.io/lgtm/grade/python/github/wang0618/PyWebIO.svg?colorB=brightgreen" alt="Python code quality">
    </a>
    <a href="https://lgtm.com/projects/g/wang0618/PyWebIO/context:javascript">
        <img src="https://img.shields.io/lgtm/grade/javascript/github/wang0618/PyWebIO.svg?colorB=brightgreen" alt="Javascript code quality">
    </a>
    <a href="https://github.com/wang0618/PyWebIO/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/wang0618/PyWebIO.svg" alt="License">
    </a>
    <br/>
    <a href="https://pywebio.readthedocs.io/zn_CN/latest/">[Document]</a> | <a href="http://pywebio-demos.demo.wangweimin.site/">[Demos]</a> | <a href="https://github.com/wang0618/PyWebIO/wiki/%5B%E4%B8%AD%E6%96%87%5D-Why-PyWebIO%3F">[Why PyWebIO?]</a>
</p>

[English](#pywebio-en) | [中文](#pywebio-zh)

PyWebIO提供了一系列命令式的交互函数来在浏览器上获取用户输入和进行输出，将浏览器变成了一个“富文本终端”，可以用于构建简单的Web应用或基于浏览器的GUI应用。
PyWebIO还可以方便地整合进现有的Web服务，让你不需要编写HTML和JS代码，就可以构建出具有良好可用性的应用。

<p align="center">
    <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/output_demo.gif" alt="PyWebIO output demo" width='609px'/>
    <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/input_demo.gif" alt="PyWebIO input demo" width='609px'/>
</p>


功能特性：

- 使用同步而不是基于回调的方式获取输入，代码编写逻辑更自然
- 非声明式布局，布局方式简单高效
- 代码侵入性小，旧脚本代码仅需修改输入输出逻辑便可改造为Web服务
- 支持整合到现有的Web服务，目前支持与Flask、Django、Tornado、aiohttp框架集成
- 同时支持基于线程的执行模型和基于协程的执行模型
- 支持结合第三方库实现数据可视化

## Installation

稳定版安装:

```bash
pip3 install -U pywebio
```

开发版安装:
```bash
pip3 install -U https://code.aliyun.com/wang0618/pywebio/repository/archive.zip
```

**系统要求**: PyWebIO要求 Python 版本在 3.5.2 及以上

## Quick start

**Hello, world**

这是一个使用PyWebIO计算 [BMI指数](https://en.wikipedia.org/wiki/Body_mass_index) 的脚本:

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


如果没有使用PyWebIO，这只是一个非常简单的脚本，而通过使用PyWebIO提供的输入输出函数，你可以在浏览器中与代码进行交互 [[demo]](http://pywebio-demos.demo.wangweimin.site/bmi)：

<p align="center">
    <a href="http://pywebio-demos.demo.wangweimin.site/?pywebio_api=bmi">
        <img src="https://raw.githubusercontent.com/wang0618/PyWebIO/dev/docs/assets/demo_zh.gif" alt="PyWebIO demo" width="400px"/>
    </a>
</p>

**作为Web服务提供**

上文BMI程序会在计算完毕后立刻退出，可以使用 [`pywebio.start_server()`](https://pywebio.readthedocs.io/zh_CN/latest/platform.html#pywebio.platform.tornado.start_server) 将 `bmi()` 函数作为Web服务提供：

```python
from pywebio import start_server
from pywebio.input import input, FLOAT
from pywebio.output import put_text

def bmi():  # bmi() 函数内容不变
    ...  

if __name__ == '__main__':
    start_server(bmi, port=80)
```

**与现有Web框架整合**

Tornado应用整合：仅需在现有的Tornado应用中添加一个 `RequestHandler` ，就可以将PyWebIO应用整合进Tornado Web服务中

```python
import tornado.ioloop
import tornado.web
from pywebio.platform.tornado import webio_handler

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/bmi", webio_handler(bmi)),  # bmi 即为上文计算BMI指数的函数
    ])
    application.listen(port=80, address='localhost')
    tornado.ioloop.IOLoop.current().start()
```

在 `http://localhost/bmi` 页面上就可以计算BMI了。

与其他Web框架整合请见[文档](https://pywebio.readthedocs.io/zh_CN/latest/guide.html#web)

## Demos

 - [基本demo](http://pywebio-demos.demo.wangweimin.site/) : 包含PyWebIO基本输入输出演示和使用PyWebIO编写的小应用
 - [数据可视化demo](http://pywebio-charts.demo.wangweimin.site/) : 使用 bokeh、plotly、pyecharts 等库进行数据可视化

## Document

使用手册和实现文档见 [https://pywebio.readthedocs.io](https://pywebio.readthedocs.io/zh_CN/latest/)

