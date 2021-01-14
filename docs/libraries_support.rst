第三方库生态
==============

.. _visualization:

数据可视化
-------------
PyWebIO支持使用第三方库进行数据可视化

Bokeh
^^^^^^^^^^^^^^^^^^^^^^
`Bokeh <https://github.com/bokeh/bokeh>`_ 是一个支持创建实时交互的数据可视化库。

在 PyWebIO 会话中调用 ``bokeh.io.output_notebook(notebook_type='pywebio')`` 来设置Bokeh输出到PyWebIO::

    from bokeh.io import output_notebook
    from bokeh.io import show

    output_notebook(notebook_type='pywebio')
    fig = figure(...)
    ...
    show(fig)

相应demo见 :charts_demo_host:`bokeh demo </?app=bokeh>`

除了创建普通图表，Bokeh还可以通过启动Bokeh server来显示Bokeh app，Bokeh app支持向图表的添加按钮、输入框等交互组件，并向组件注册Python回调，从而创建可以与Python代码交互的图表。

在PyWebIO中，你也可以使用 ``bokeh.io.show()`` 来显示一个Bokeh App，代码示例见 `bokeh_app.py <https://github.com/wang0618/PyWebIO/blob/master/demos/bokeh_app.py>`_。

.. image:: https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/bokeh.png

pyecharts
^^^^^^^^^^^^^^^^^^^^^^
`pyecharts <https://github.com/pyecharts/pyecharts>`_ 是一个使用Python创建 `Echarts <https://github.com/ecomfe/echarts>`_ 可视化图表的库。

在 PyWebIO 中使用 `put_html() <pywebio.output.put_html>` 可以输出 pyecharts 库创建的图表::

    # chart 为 pyecharts 的图表实例
    pywebio.output.put_html(chart.render_notebook())

相应demo见 :charts_demo_host:`pyecharts demo </?app=pyecharts>`

.. only:: not latex

    .. image:: https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/pyecharts.gif

plotly
^^^^^^^^^^^^^^^^^^^^^^
`plotly.py <https://github.com/plotly/plotly.py>`_ 是一个非常流行的Python数据可视化库，可以生成高质量的交互式图表。

PyWebIO 支持输出使用 plotly 库创建的图表。使用方式为在PyWebIO会话中调用::

    # fig 为 plotly 的图表实例
    html = fig.to_html(include_plotlyjs="require", full_html=False)
    pywebio.output.put_html(html)

相应demo见 :charts_demo_host:`plotly demo </?app=plotly>`

.. image:: https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/plotly.png

cutecharts.py
^^^^^^^^^^^^^^^^^^^^^^

`cutecharts.py <https://github.com/cutecharts/cutecharts.py>`_ 是一个可以创建具有卡通风格的可视化图表的python库。
底层使用了 `chart.xkcd <https://github.com/timqian/chart.xkcd>`_ Javascript库。

在 PyWebIO 中使用 `put_html() <pywebio.output.put_html>` 可以输出 cutecharts.py 库创建的图表::

    # chart 为 cutecharts 的图表实例
    pywebio.output.put_html(chart.render_notebook())

相应demo见 :charts_demo_host:`cutecharts demo </?app=cutecharts>`

.. image:: https://cdn.jsdelivr.net/gh/wang0618/pywebio-chart-gallery@master/assets/cutecharts.png
