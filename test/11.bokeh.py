import subprocess

import time
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

    # output to static HTML file
    # output_file("log_lines.html")

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

    # save(p)


def datatable():
    from datetime import date
    from random import randint

    from bokeh.io import show
    from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn

    data = dict(
        dates=[date(2014, 3, i + 1) for i in range(10)],
        downloads=[randint(0, 100) for i in range(10)],
    )
    source = ColumnDataSource(data)

    columns = [
        TableColumn(field="dates", title="Date", formatter=DateFormatter()),
        TableColumn(field="downloads", title="Downloads"),
    ]
    data_table = DataTable(source=source, columns=columns, width=400, height=280)

    show(data_table)


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


def target():
    from bokeh.io import output_notebook
    from bokeh.io import show

    output_notebook(verbose=False, notebook_type='pywebio')

    put_markdown('## Basic doc')
    basci_doc()

    put_markdown('## App')
    show(bkapp, notebook_url='localhost:8080')

    put_markdown('## App again')
    show(bkapp, notebook_url='localhost:8080')

    put_markdown('## Widgets')
    widgets()


def test(server_proc: subprocess.Popen, browser: Chrome):
    time.sleep(3)
    percySnapshot(browser=browser, name='bokeh')


def start_test_server():
    pywebio.enable_debug()
    start_server(target, port=8080, debug=True, auto_open_webbrowser=False)


if __name__ == '__main__':
    util.run_test(start_test_server, test)
