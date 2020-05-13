from bokeh.io import output_notebook
from bokeh.io import show
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

from pywebio import start_server
from pywebio.output import *


def bkapp(doc):
    df = sea_surface_temperature.copy()
    source = ColumnDataSource(data=df)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line('time', 'temperature', source=source)

    def callback(attr, old, new):
        if new == 0:
            data = df
        else:
            data = df.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column([slider, plot], sizing_mode='stretch_width'))


def main():
    output_notebook(verbose=False, notebook_type='pywebio')

    put_markdown("""# Bokeh Applications in PyWebIO
    
    [Bokeh Applications](https://docs.bokeh.org/en/latest/docs/user_guide/server.html) 支持向图表的添加按钮、输入框等交互组件，并向组件添加Python回调，从而创建可以与Python代码交互的可视化图表。
    
    在PyWebIO中，你也可以使用 `bokeh.io.show()` 来显示一个Bokeh App，和输出普通图表一样，只需要在会话开始时调用 `bokeh.io.output_notebook(notebook_type='pywebio')` 来设置PyWebIO输出环境。
    
    以下为一个 Bokeh App demo:
    
    """, lstrip=True)

    show(bkapp)


if __name__ == '__main__':
    start_server(main, port=8080, debug=True)
