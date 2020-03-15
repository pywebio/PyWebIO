## PyWebIO

PyWebIO，一个用于在浏览器上获取输入和进行输出的工具库。能够将原有的通过终端交互的脚本快速服务化，供其他人在网络通过浏览器使用；PyWebIO还可以方便地整合进现有的Web服务，非常适合于构建对UI要求不高的后端服务的功能原型。

特点：

- 使用同步而不是基于回调的方式获取输入，无需在各个步骤之间保存状态，直观、方便
- 代码侵入性小
- 支持并发请求
- 支持状态恢复
- 支持整合到现有的Web服务，目前支持与Tronado的集成

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

现在如何快速让别人也可以使用你编写的功能？很简单，只需要把脚本启动，然后把电脑拿给其他人用就好了，本教程到此结束 (笑)

我们来看一下使用PyWebIO改造后的代码：

```python
# BMI.py
from pywebio.input import input  # 1
from pywebio.output import put_text  # 1
from pywebio.ioloop import start_ioloop

async def bmi():  # 2
    height = await input("请输入你的身高(cm)：")  # 3
    weight = await input("请输入你的体重(kg)：")  # 3

    BMI = float(weight) / (float(height) / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            put_text('你的 BMI 值: %.1f，身体状态：%s' % (BMI, status))  # 4
            break

if __name__ == '__main__':
    start_ioloop(bmi)  # 5
```

代码运行起来后，浏览器打开`http://localhost:8080`后，便可以像下面所示来使用脚本了。

![file](/docs/assets/demo.gif)

我们来看一下改造后的代码和原代码的变化，一共有5处修改(通过注释标出)：

1处是引入PyWebIO库中要使用的函数。

2处我们用 `async def` 对函数进行了声明，表示该函数是异步的，在Python中，这样的函数叫做协程函数，这是Python3.5引入的新特性，与普通函数相比，协程函数可以在函数体中使用`await`语法等待一个异步操作的完成。

3处，我们将原来直接对内置函数`input`的调用改成了使用`await`调用PyWebIO库提供的`input`函数，PyWebIO库提供的`input`函数功能更多，并且PyWebIO在等待当前用户进行输入时，程序同时可以对其他用户的请求进行响应，也就是说，PyWebIO支持多用户同时在浏览器中使用脚本。

4处我们将原本使用内置`print`输出到控制台的操作改成了使用PyWebIO库提供的`text_print`函数输出文本到浏览器

最后，在5处，我们改变了函数的运行方式，将直接调用改成了传入`start_ioloop`函数启动服务。

到这里你大概已经明白PyWebIO库的功能了，简单的说，我们只需要将原脚本中输入和输出的部分替换成PyWebIO库提供的函数，就可以让脚本可以通过浏览器访问了。


## Overview

```bash
python3 -m pywebio.demos.overview-zh
```
Then open `http://localhost:8080/` in Web browser 