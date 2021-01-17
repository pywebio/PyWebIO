PyWebIO
==========

PyWebIO提供了一系列命令式的交互函数来在浏览器上获取用户输入和进行输出，将浏览器变成了一个“富文本终端”，可以用于构建简单的Web应用或基于浏览器的GUI应用。
使用PyWebIO，开发者能像编写终端脚本一样(基于input和print进行交互)来编写应用，无需具备HTML和JS的相关知识；
PyWebIO还可以方便地整合进现有的Web框架。非常适合快速构建对UI要求不高的应用。


特性
------------

- 使用同步而不是基于回调的方式获取输入，代码编写逻辑更自然
- 非声明式布局，布局方式简单高效
- 代码侵入性小，旧脚本代码仅需修改输入输出逻辑便可改造为Web服务
- 支持整合到现有的Web服务，目前支持与Flask、Django、Tornado、aiohttp框架集成
- 同时支持基于线程的执行模型和基于协程的执行模型
- 支持结合第三方库实现数据可视化

Install
------------

稳定版安装::

   pip3 install -U pywebio

开发版安装::

    pip3 install -U --force-reinstall https://code.aliyun.com/wang0618/pywebio/repository/archive.zip

**系统要求**: PyWebIO要求 Python 版本在 3.5.2 及以上

.. _hello_word:

Hello, world
--------------

这是一个使用PyWebIO计算 `BMI指数 <https://en.wikipedia.org/wiki/Body_mass_index>`_ 的脚本::

    # A simple script to calculate BMI
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

如果没有使用PyWebIO，这只是一个非常简单的脚本，而通过使用PyWebIO提供的输入输出函数，你可以在浏览器中与代码进行交互：

.. image:: /assets/demo.*
   :width: 450px
   :align: center

将上面代码最后一行对 ``bmi()`` 的直接调用改为使用 `pywebio.start_server(bmi, port=80) <pywebio.platform.tornado.start_server>` 便可以在80端口提供 ``bmi()`` 服务( :demo_host:`在线Demo </?pywebio_api=bmi>` )。

将 ``bmi()`` 服务整合到现有的Web框架请参考 :ref:`与Web框架集成 <integration_web_framework>`

Documentation
-------------
这个文档同时也提供 `PDF 和 Epub 格式 <https://readthedocs.org/projects/pywebio/downloads/>`_.

.. toctree::
   :maxdepth: 2
   :caption: 使用手册

   guide
   input
   output
   session
   platform
   libraries_support
   demos
   misc

.. toctree::
   :titlesonly:

   releases

.. toctree::
   :maxdepth: 2
   :caption: 实现文档

   spec

Indices and tables
----------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Discussion and support
----------------------

* Need help when use PyWebIO? Make a new discussion on `Github Discussions <https://github.com/wang0618/PyWebIO/discussions>`_.

* Report bugs on the `GitHub issue <https://github.com/wang0618/pywebio/issues>`_.

