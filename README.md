## PyWebIO

PyWebIO是一个用于在浏览器上获取输入和进行输出的工具库。通过浏览器来提供更多输入输出方式，能够将原有的通过终端交互的脚本快速服务化，供其他人在网络上通过浏览器访问使用；PyWebIO还可以方便地整合进现有的Web服务，非常适合于构建对UI要求不高的后端服务。

特点：

- 使用同步而不是基于回调的方式获取输入，无需在各个步骤之间保存状态，使用更方便
- 代码侵入性小，对于旧脚本代码仅需修改输入输出逻辑
- 支持多用户与并发请求
- 支持整合到现有的Web服务，目前支持与Tornado和Flask的集成
- 同时支持基于线程的执行模型和基于协程的执行模型

## Install

```bash
pip3 install pywebio
```

## Quick start

假设你编写了如下脚本来计算[BMI指数](https://en.wikipedia.org/wiki/Body_mass_index)：

```python
# BMI.py
def bmi():
    height = input("请输入你的身高(cm)：")
    weight = input("请输入你的体重(kg)：")

    BMI = float(weight) / (float(height) / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            print('你的 BMI 值: %.1f，身体状态：%s' % (BMI, status))
            break

if __name__ == '__main__':
    bmi()
```

### 在浏览器中进行输入输出

仅仅需将输入、输出函数替换成`PyWebIO`的输入输出函数就完成了改造(下面代码通过注释标出了改动部分)

```python
# BMI.py
from pywebio.input import input  # Change 1
from pywebio.output import put_text  # Change 1

def bmi():
    height = input("请输入你的身高(cm)：")  # Change 2
    weight = input("请输入你的体重(kg)：")  # Change 2

    BMI = float(weight) / (float(height) / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            put_text('你的 BMI 值: %.1f，身体状态：%s' % (BMI, status))  # Change 3
            break

if __name__ == '__main__':
    bmi()
```

运行代码就可以在自动弹出的浏览器中与代码交互了：

![file](/docs/assets/demo.gif)

### 向外提供服务
上文对使用`PyWebIO`进行改造的程序，运行模式还是脚本，程序计算完毕后立刻退出。可以使用 `pywebio.start_server` 将程序功能作为Web服务提供：

```python
# BMI.py
from pywebio import start_server
from pywebio.input import input 
from pywebio.output import put_text 

def bmi():
    height = input("请输入你的身高(cm)：") 
    weight = input("请输入你的体重(kg)：") 

    BMI = float(weight) / (float(height) / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            put_text('你的 BMI 值: %.1f，身体状态：%s' % (BMI, status))
            break

if __name__ == '__main__':
    start_server(bmi)
```

### 与现有Web框架整合
仅需在现有的`Tornado`应用中加入加入两个`RequestHandler`，就可以将使用`PyWebIO`编写的函数整合进`Tornado`应用中了

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
        (r"/bmi/io", webio_handler(bmi)),  # bmi 即为上文中使用`PyWebIO`进行改造的函数
        (r"/bmi/(.*)", tornado.web.StaticFileHandler, {"path": STATIC_PATH, 'default_filename': 'index.html'})
    ])
    application.listen(port=80, address='localhost')
    tornado.ioloop.IOLoop.current().start()
```
在 `http://localhost/bmi/` 页面上就可以计算BMI了

## Overview
`PyWebIO`支持丰富的输入输出形式，可以运行以下命令进行速览：

```bash
python3 -m pywebio.demos.zh.overview
```
