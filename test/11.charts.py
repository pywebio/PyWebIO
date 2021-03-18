import subprocess
import time

import plotly.graph_objects as go
from cutecharts.charts import Bar
from cutecharts.charts import Line
from cutecharts.charts import Pie
from cutecharts.charts import Radar
from percy import percySnapshot
from selenium.webdriver import Chrome

import pywebio
import util
from pywebio import start_server
from pywebio.output import *


def bkapp(doc):
    import yaml

    from bokeh.layouts import column
    from bokeh.models import ColumnDataSource, Slider
    from bokeh.plotting import figure
    from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
    from bokeh.themes import Theme
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

    doc.add_root(column(slider, plot))

    doc.theme = Theme(json=yaml.load("""
       attrs:
           Figure:
               background_fill_color: "#DDDDDD"
               outline_line_color: white
               toolbar_location: above
               height: 500
               width: 800
           Grid:
               grid_line_dash: [6, 4]
               grid_line_color: white
   """, Loader=yaml.FullLoader))


def basci_doc():
    from bokeh.io import show
    from bokeh.plotting import figure
    # prepare some data
    x = [0.1, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    y0 = [i ** 2 for i in x]
    y1 = [10 ** i for i in x]
    y2 = [10 ** (i ** 2) for i in x]

    # create a new plot
    p = figure(
        tools="pan,box_zoom,reset,save",
        y_axis_type="log", y_range=[0.001, 10 ** 11], title="log axis example",
        x_axis_label='sections', y_axis_label='particles'
    )

    # add some renderers
    p.line(x, x, legend_label="y=x")
    p.circle(x, x, legend_label="y=x", fill_color="white", size=8)
    p.line(x, y0, legend_label="y=x^2", line_width=3)
    p.line(x, y1, legend_label="y=10^x", line_color="red")
    p.circle(x, y1, legend_label="y=10^x", fill_color="red", line_color="red", size=6)
    p.line(x, y2, legend_label="y=10^x^2", line_color="orange", line_dash="4 4")

    # show the results
    show(p)


def widgets():
    from bokeh.io import show
    from bokeh.models import Select, CheckboxButtonGroup, Button, CheckboxGroup, ColorPicker, Dropdown, \
        FileInput, MultiSelect, RadioButtonGroup, RadioGroup, Slider, RangeSlider, TextAreaInput, TextInput, Toggle, \
        Paragraph, PreText, Div

    put_text('Button')
    button = Button(label="Foo", button_type="success")
    show(button)

    put_text('CheckboxButtonGroup')
    checkbox_button_group = CheckboxButtonGroup(
        labels=["Option 1", "Option 2", "Option 3"], active=[0, 1])
    show(checkbox_button_group)

    put_text('CheckboxGroup')
    checkbox_group = CheckboxGroup(
        labels=["Option 1", "Option 2", "Option 3"], active=[0, 1])
    show(checkbox_group)

    put_text('ColorPicker')
    color_picker = ColorPicker(color="#ff4466", title="Choose color:", width=200)
    show(color_picker)

    put_text('Dropdown')
    menu = [("Item 1", "item_1"), ("Item 2", "item_2"), None, ("Item 3", "item_3")]
    dropdown = Dropdown(label="Dropdown button", button_type="warning", menu=menu)
    show(dropdown)

    put_text('FileInput')
    file_input = FileInput()
    show(file_input)

    put_text('MultiSelect')
    multi_select = MultiSelect(title="Option:", value=["foo", "quux"],
                               options=[("foo", "Foo"), ("bar", "BAR"), ("baz", "bAz"), ("quux", "quux")])
    show(multi_select)

    put_text('RadioButtonGroup')
    radio_button_group = RadioButtonGroup(
        labels=["Option 1", "Option 2", "Option 3"], active=0)
    show(radio_button_group)

    put_text('RadioGroup')
    radio_group = RadioGroup(
        labels=["Option 1", "Option 2", "Option 3"], active=0)
    show(radio_group)

    put_text('Select')
    select = Select(title="Option:", value="foo", options=["foo", "bar", "baz", "quux"])
    show(select)

    put_text('Slider')
    slider = Slider(start=0, end=10, value=1, step=.1, title="Stuff")
    show(slider)

    put_text('RangeSlider')
    range_slider = RangeSlider(start=0, end=10, value=(1, 9), step=.1, title="Stuff")
    show(range_slider)

    put_text('TextAreaInput')
    text_input = TextAreaInput(value="default", rows=6, title="Label:")
    show(text_input)

    put_text('TextInput')
    text_input = TextInput(value="default", title="Label:")
    show(text_input)

    put_text('Toggle')
    toggle = Toggle(label="Foo", button_type="success")
    show(toggle)

    put_text('Div')
    div = Div(text="""Your <a href="https://en.wikipedia.org/wiki/HTML">HTML</a>-supported text is initialized with the <b>text</b> argument.  The
    remaining div arguments are <b>width</b> and <b>height</b>. For this example, those values
    are <i>200</i> and <i>100</i> respectively.""",
              width=200, height=100)
    show(div)

    put_text('Paragraph')
    p = Paragraph(text="""Your text is initialized with the 'text' argument.  The
    remaining Paragraph arguments are 'width' and 'height'. For this example, those values
    are 200 and 100 respectively.""",
                  width=200, height=100)
    show(p)

    put_text('PreText')
    pre = PreText(text="""Your text is initialized with the 'text' argument.

    The remaining Paragraph arguments are 'width' and 'height'. For this example,
    those values are 500 and 100 respectively.""",
                  width=500, height=100)
    show(pre)


def pyecharts():
    from pyecharts.charts import Bar
    from pyecharts.faker import Faker
    from pyecharts import options as opts
    from pyecharts.charts import Polar
    from pyecharts.charts import HeatMap
    from pyecharts.charts import Tree
    from pyecharts.globals import CurrentConfig

    CurrentConfig.ONLINE_HOST = "https://cdn.jsdelivr.net/gh/pyecharts/pyecharts-assets@master/assets/"

    r1 = ['草莓', '芒果', '葡萄', '雪梨', '西瓜', '柠檬', '车厘子']
    r2 = [127, 33, 110, 29, 146, 121, 36]
    r3 = [25, 87, 114, 131, 130, 94, 146]
    c1 = (
        Bar({"width": "100%"})
            .add_xaxis(r1)
            .add_yaxis("商家A", r2)
            .add_yaxis("商家B", r3)
            .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
    )

    c2 = (
        Polar({"width": "100%"})
            .add_schema(
            radiusaxis_opts=opts.RadiusAxisOpts(data=Faker.week, type_="category"),
            angleaxis_opts=opts.AngleAxisOpts(is_clockwise=True, max_=10),
        )
            .add("A", [1, 2, 3, 4, 3, 5, 1], type_="bar")
            .set_global_opts(title_opts=opts.TitleOpts(title="Polar-RadiusAxis"))
            .set_series_opts(label_opts=opts.LabelOpts(is_show=True))

    )

    data = [
        {
            "children": [
                {"name": "B"},
                {
                    "children": [{"children": [{"name": "I"}], "name": "E"}, {"name": "F"}],
                    "name": "C",
                },
                {
                    "children": [
                        {"children": [{"name": "J"}, {"name": "K"}], "name": "G"},
                        {"name": "H"},
                    ],
                    "name": "D",
                },
            ],
            "name": "A",
        }
    ]

    c3 = (
        Tree({"width": "100%"})
            .add("", data)
            .set_global_opts(title_opts=opts.TitleOpts(title="Tree-基本示例"))

    )

    value = [[i, j, int(i * j * 3.14 * 314 % 50)] for i in range(24) for j in range(7)]
    c4 = (
        HeatMap({"width": "100%"})
            .add_xaxis(Faker.clock)
            .add_yaxis(
            "series0",
            Faker.week,
            value,
            label_opts=opts.LabelOpts(is_show=True, position="inside"),
        )
            .set_global_opts(
            title_opts=opts.TitleOpts(title="HeatMap-Label 显示"),
            visualmap_opts=opts.VisualMapOpts(),
        )

    )

    put_grid([
        [put_html(c1.render_notebook()), put_html(c2.render_notebook())],
        [put_html(c3.render_notebook()), put_html(c4.render_notebook())]
    ], cell_width='1fr', cell_height='1fr')


def cutecharts():
    def radar_base():
        chart = Radar("Radar-基本示例", width="100%")
        chart.set_options(labels=["草莓", "芒果", "葡萄", "雪梨", "西瓜", "柠檬", "车厘子"])
        chart.add_series("series-A", [25, 87, 114, 131, 130, 94, 146])
        chart.add_series("series-B", [25, 87, 114, 131, 130, 94, 146])
        return put_html(chart.render_notebook())

    def pie_base():
        chart = Pie("Pie-基本示例", width="100%")
        chart.set_options(labels=["小米", "三星", "华为", "苹果", "魅族", "VIVO", "OPPO"])
        chart.add_series([25, 87, 114, 131, 130, 94, 146])
        return put_html(chart.render_notebook())

    def line_base():
        chart = Line("Line-基本示例", width="100%")
        chart.set_options(labels=["衬衫", "毛衣", "领带", "裤子", "风衣", "高跟鞋", "袜子"], x_label="I'm xlabel", y_label="I'm ylabel")
        chart.add_series("series-A", [25, 87, 114, 131, 130, 94, 146])
        chart.add_series("series-B", [127, 33, 110, 29, 146, 121, 36])
        return put_html(chart.render_notebook())

    def bar_base():
        chart = Bar("Bar-基本示例", width="100%")
        chart.set_options(labels=["可乐", "雪碧", "橙汁", "绿茶", "奶茶", "百威", "青岛"], x_label="I'm xlabel", y_label="I'm ylabel")
        chart.add_series("series-A", [127, 33, 110, 29, 146, 121, 36])
        return put_html(chart.render_notebook())

    put_grid([[bar_base(), line_base()], [pie_base(), radar_base()]], cell_width='1fr', cell_height='1fr')


def plotly():
    x = list(range(10))

    fig = go.Figure(data=go.Scatter(x=x, y=[i ** 2 for i in x]))
    html1 = fig.to_html(include_plotlyjs="require", full_html=False)

    fig = go.Figure(data=[go.Scatter(
        x=[1, 2, 3, 4], y=[10, 11, 12, 13],
        mode='markers',
        marker=dict(
            color=['rgb(93, 164, 214)', 'rgb(255, 144, 14)',
                   'rgb(44, 160, 101)', 'rgb(255, 65, 54)'],
            opacity=[1, 0.8, 0.6, 0.4],
            size=[40, 60, 80, 100],
        )
    )])

    html2 = fig.to_html(include_plotlyjs="require", full_html=False)

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node={
            "label": ["A", "B", "C", "D", "E", "F"],
            "x": [0.2, 0.1, 0.5, 0.7, 0.3, 0.5],
            "y": [0.7, 0.5, 0.2, 0.4, 0.2, 0.3],
            'pad': 10},  # 10 Pixels
        link={
            "source": [0, 0, 1, 2, 5, 4, 3, 5],
            "target": [5, 3, 4, 3, 0, 2, 2, 3],
            "value": [1, 2, 1, 1, 1, 1, 1, 2]}))

    html3 = fig.to_html(include_plotlyjs="require", full_html=False)

    fig = go.Figure(go.Sunburst(
        labels=["Eve", "Cain", "Seth", "Enos", "Noam", "Abel", "Awan", "Enoch", "Azura"],
        parents=["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve"],
        values=[10, 14, 12, 10, 2, 6, 6, 4, 4],
    ))
    # Update layout for tight margin
    # See https://plotly.com/python/creating-and-updating-figures/
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))

    html4 = fig.to_html(include_plotlyjs="require", full_html=False)

    put_grid([
        [put_html(html1), put_html(html2)],
        [put_html(html3), put_html(html4)]
    ], cell_width='1fr', cell_height='1fr')


def target():
    from bokeh.io import output_notebook
    from bokeh.io import show

    output_notebook(verbose=True, notebook_type='pywebio')

    put_markdown('# Bokeh')

    put_markdown('## Basic doc')
    basci_doc()

    put_markdown('## App')
    show(bkapp)

    put_markdown('## App again')
    show(bkapp)

    put_markdown('## Widgets')
    widgets()

    put_markdown('# pyecharts')
    pyecharts()

    put_markdown('# cutecharts')
    cutecharts()

    put_markdown('# plotly')
    plotly()


def test(server_proc: subprocess.Popen, browser: Chrome):
    time.sleep(8)
    percySnapshot(browser, name='bokeh')


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, auto_open_webbrowser=False, cdn=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
