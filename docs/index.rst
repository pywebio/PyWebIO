PyWebIO
==========
PyWebIO是一个用于在浏览器上获取输入和进行输出的工具库。通过浏览器来提供更多输入输出方式，你可以将原有的通过终端交互的脚本快速服务化，供其他人在网络上通过浏览器访问使用；PyWebIO还可以方便地整合进现有的Web服务，非常适合于构建对UI要求不高的后端服务。


特点：
------------

- 使用同步而不是基于回调的方式获取输入，无需在各个步骤之间保存状态，使用更方便
- 代码侵入性小，对于旧脚本代码仅需修改输入输出逻辑
- 支持多用户与并发请求
- 支持整合到现有的Web服务，目前支持与Tornado和Flask的集成
- 同时支持基于线程的执行模型和基于协程的执行模型


Install
------------

::

   pip3 install pywebio

**系统要求**: PyWebIO要求 Python 版本在 3.5.2 及以上

.. _hello_word:

Hello, world
--------------

这是一个使用PywWebIO计算 `BMI指数 <https://en.wikipedia.org/wiki/Body_mass_index>`_ 的脚本::

   # A simple script to calculate BMI
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
       bmi()

如果不是程序开始的头文件，你甚至不会意识到自己正在使用一个输入输出库。

运行以上代码就可以在自动弹出的浏览器中与代码交互了：

.. image:: /assets/demo.*

将上面代码最后一行对 ``bmi()`` 的直接调用改为使用 `pywebio.start_server(bmi, port=80) <pywebio.platform.start_server>` 便可以在80端口提供 ``bmi()`` 服务。

将 ``bmi()`` 服务整合到现有的Web 框架请参考 :ref:`与Web框架集成 <integration_web_framework>`

Documentation
-------------
这个文档同时也提供 `PDF 和 Epub 格式 <https://readthedocs.org/projects/pywebio/downloads/>`_.

.. toctree::
   :maxdepth: 3
   :caption: 使用手册

   guide
   input
   output
   session
   server
   misc

.. toctree::
   :maxdepth: 2
   :caption: 实现文档

   arch
   spec

Indices and tables
----------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Discussion and support
----------------------

* Need help when use PyWebIO? Send me Email ``wang0.618&qq.com`` (replace ``&`` whit ``@`` ).

* Report bugs on the `GitHub issue <https://github.com/wang0618/pywebio/issues>`_.

