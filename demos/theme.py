from functools import partial

from pywebio import start_server, config
from pywebio.input import *
from pywebio.output import *
from pywebio.pin import *
from pywebio.session import *


def pin_widgets():
    put_markdown("# Pin widget")
    options = [
        {
            "label": "Option one",
            "value": 1,
            "selected": True,
        },
        {
            "label": "Option two",
            "value": 2,
        },
        {
            "label": "Disabled option",
            "value": 3,
            "disabled": True
        }
    ]
    put_input('input', label='Text input', placeholder="Enter email",
              help_text="We'll never share your email with anyone else.")
    put_input('valid_input', label="Valid input", value="correct value")
    put_input('invalid_input', label="Invalid input", value="wrong value")
    put_textarea('textarea', label='Textarea', rows=3, maxlength=10, minlength=20, value=None,
                 placeholder='This is placeholder message', readonly=False)
    put_textarea('code', label='Code area', rows=4, code={'mode': 'python'},
                 value='import pywebio\npywebio.output.put_text("hello world")')
    put_select('select', options=options, label='Select')
    put_select('select_multiple', options=options, label='Multiple select', multiple=True, value=None)
    put_checkbox('checkbox', options=options, label='Checkbox', inline=False, value=None)
    put_checkbox('checkbox_inline', options=options, label='Inline checkbox', inline=True, value=None)
    put_radio('radio', options=options, label='Radio', inline=False, value=None)
    put_radio('radio_inline', options=options, label='Inline radio', inline=True, value='B')
    put_slider('slider', label='Slider')
    put_actions('actions', buttons=[
        {'label': 'Submit', 'value': '1'},
        {'label': 'Warning', 'value': '2', 'color': 'warning'},
        {'label': 'Danger', 'value': '3', 'color': 'danger'},
    ], label='Actions')

    pin_update('valid_input', valid_status=True, valid_feedback="Success! You've done it.")
    pin_update('invalid_input', valid_status=False, invalid_feedback="Sorry, that username's taken. Try another?")


def form():
    options = [
        {
            "label": "Option one",
            "value": 1,
            "selected": True,
        },
        {
            "label": "Option two",
            "value": 2,
        },
        {
            "label": "Disabled option",
            "value": 3,
            "disabled": True
        }
    ]

    input_group('Input group', [
        input('Text', type=TEXT, datalist=['candidate-%s' % i for i in range(10)], name='text', required=True,
              help_text='Required'),
        input('Number', type=NUMBER, value="42", name='number'),
        input('Float', type=FLOAT, name='float'),
        input('Password', type=PASSWORD, name='password'),

        textarea('Textarea', rows=3, maxlength=20, name='textarea',
                 placeholder="The maximum number of characters you can input is 20"),

        textarea('Code', name='code', code={'mode': 'python'},
                 value='import pywebio\npywebio.output.put_text("hello world")'),

        select('Multiple select', options, name='select-multiple', multiple=True),

        select('Select', options, name='select'),

        checkbox('Inline checkbox', options, inline=True, name='checkbox-inline'),

        checkbox('Checkbox', options, name='checkbox'),

        radio('Inline radio', options, inline=True, name='radio-inline'),

        radio('Radio', options, inline=False, name='radio'),

        file_upload('File upload', name='file_upload', max_size='10m'),

        actions('Actions', [
            {'label': 'Submit', 'value': 'submit'},
            {'label': 'Disabled', 'disabled': True},
            {'label': 'Reset', 'type': 'reset', 'color': 'warning'},
            {'label': 'Cancel', 'type': 'cancel', 'color': 'danger'},
        ], name='actions'),
    ])


def output_widgets():
    ###########################################################################################
    put_markdown("# Typography")
    put_row([
        put_markdown("""
        ## Heading 2
        ### Heading 3
        #### Heading 4
        ##### Heading 5
        
        [PyWebIO](https://github.com/pywebio/PyWebIO) is awesome! 
        
        *This text will be italic*
        **This text will be bold**
        _You **can** combine them_
        ~~Strikethrough~~
        This is `inline code`
        
        As Kanye West said:
    
        > We're living the future so
        > the present is our past.
        """),

        put_markdown("""
        ### Lists
        * Item 1
        * Item 2
          * Item 2a
          * Item 2b
        
        1. Item 1
        1. Item 2
           1. Item 2a
           1. Item 2b
        
        ### Task Lists
        - [x] [links](), **formatting**, and <del>tags</del> supported
        - [x] list syntax required (any unordered or ordered list supported)
        - [x] this is a complete item
        - [ ] this is an incomplete item
        """)
    ])

    ###########################################################################################
    put_markdown("""
    # Code
    ```python
    from pywebio import *

    def main():  # PyWebIO application function
        name = input.input("what's your name")
        output.put_text("hello", name)
    
    start_server(main, port=8080, debug=True)
    ```
    """)
    ###########################################################################################
    put_markdown('# Image')
    with use_scope('image'):
        put_image(
            "https://opengraph.githubassets.com/6bcea5272d0b5901f48a67d9d05da6c7a7c7c68da32a5327943070ff9c9a3dfb/pywebio/PyWebIO").style("""
        max-height: 250px;
        border: 2px solid #fff;
        border-radius: 25px;
        """)
    ###########################################################################################
    put_markdown("# Buttons")
    # small=None, link_style=False, outline=False, group=False
    put_buttons([
        dict(label=i, value=i, color=i)
        for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    ], onclick=lambda b: toast(f'Clicked {b} button'))

    put_buttons([
        dict(label=i, value=i, color=i)
        for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    ], onclick=lambda b: toast(f'Clicked {b} button'), small=True)

    put_buttons([
        dict(label=i, value=i, color=i)
        for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    ], onclick=lambda b: toast(f'Clicked {b} button'), link_style=True)

    put_buttons([
        dict(label=i, value=i, color=i)
        for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    ], onclick=lambda b: toast(f'Clicked {b} button'), outline=True)
    put_buttons([
        dict(label=i, value=i, color=i)
        for i in ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
    ], onclick=lambda b: toast(f'Clicked {b} button'), group=True)
    ###########################################################################################
    put_markdown('# Tables')
    put_markdown("""
    First Header | Second Header
    ------------ | -------------
    Content from cell 1 | Content from cell 2
    Content in the first column | Content in the second column
    """)

    put_table([
        ['Type', 'Content'],
        ['text', '<hr/>'],
        ['html', put_html('X<sup>2</sup>')],
        ['buttons', put_buttons(['A', 'B'], onclick=toast, small=True)],
        ['markdown', put_markdown('`awesome PyWebIO!`\n - 1\n - 2\n - 3')],
        ['file', put_file('hello.text', b'')],
        ['table', put_table([
            ['A', 'B'],
            [put_markdown('`C`'), put_markdown('`D`')]
        ])]
    ])
    ###########################################################################################
    put_markdown('# Popup')

    def show_popup():
        popup('Popup title', [
            'Popup body text goes here.',
            put_table([
                ['Type', 'Content'],
                ['html', put_html('X<sup>2</sup>')],
                ['text', '<hr/>'],
                ['buttons', put_buttons(['A', 'B'], onclick=toast)],
                ['markdown', put_markdown('`Awesome PyWebIO!`')],
                ['file', put_file('hello.text', b'')],
                ['table', put_table([['A', 'B'], ['C', 'D']])]
            ]),
            put_button('Close', onclick=close_popup, outline=True)
        ], size=PopupSize.NORMAL)

    put_button("Click me to show a popup", onclick=show_popup)

    ###########################################################################################
    put_markdown('# Layout')
    put_row([
        put_column([
            put_code('A'),
            put_row([
                put_code('B1'), None,
                put_code('B2'), None,
                put_code('B3'),
            ]),
            put_code('C'),
        ]), None,
        put_code('python'), None,
        put_code('python\n' * 20).style('max-height:200px;'),
    ])

    ###########################################################################################
    put_markdown('# Loading')
    put_processbar('processbar', 0.3)
    put_text()
    put_grid([
        [
            put_loading(shape=shape, color=color)
            for color in ('primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark')
        ]
        for shape in ('border', 'grow')
    ], cell_width='50px', cell_height='50px')
    ###########################################################################################
    put_markdown('# Tabs')

    put_tabs([
        {'title': 'Text', 'content': 'Hello world'},
        {'title': 'Markdown', 'content': put_markdown('~~Strikethrough~~')},
        {'title': 'More content', 'content': [
            put_table([
                ['Commodity', 'Price'],
                ['Apple', '5.5'],
                ['Banana', '7'],
            ]),
            put_link('pywebio', 'https://github.com/wang0618/PyWebIO')
        ]},
    ])
    ###########################################################################################
    put_markdown('# Scrollable')

    put_scrollable("Long text " * 200, height=200)
    ###########################################################################################
    put_markdown('# Collapse')
    put_collapse('Click to expand', [
        'text',
        put_markdown('~~Strikethrough~~'),
        put_table([
            ['Commodity', 'Price'],
            ['Apple', '5.5'],
        ])
    ])
    ###########################################################################################
    put_markdown('# Message')

    put_warning(
        put_markdown('### Warning!'),
        "Best check yo self, you're not looking too good. Nulla vitae elit libero, a pharetra augue. Praesent commodo cursus magna, vel scelerisque nisl consectetur et.",
        closable=True)
    put_success("Well done! You successfully read this important alert message.")
    put_info("Heads up! This alert needs your attention, but it's not super important.")
    put_error("Oh snap! Change a few things up and try submitting again.")


ALL_THEME = ('default', 'dark', 'sketchy', 'minty', 'yeti')

THEME_SUMMARY = {'default': 'The default theme', 'dark': 'A theme for night',
                 'sketchy': 'A hand-drawn look for mockups and mirth', 'minty': 'A fresh feel',
                 'yeti': 'A friendly foundation'}

style = """
table img:hover {
    transition-duration: 400ms;
    transform: translateY(-2px);
    box-shadow: 0px 2px 9px 2px rgb(0 0 0 / 27%), 0 30px 50px -30px rgb(0 0 0 / 30%)
}
.page-header h1 {
    font-size: 3em;
}
#pywebio-scope-image img {
    box-shadow: rgb(204 204 204) 3px 3px 13px;
}
.webio-theme-dark #pywebio-scope-image img {
    box-shadow: none !important;
}
"""


@config(css_style=style)
def page():
    """PyWebIO Theme Preview"""

    theme = eval_js("new URLSearchParams(window.location.search).get('app')")
    if theme not in ALL_THEME:
        theme = 'default'

    put_html(f"""
    <div class="page-header">
        <div style="text-align: center">
            <h1>{theme[0].upper() + theme[1:]}</h1>
            <p class="lead">{THEME_SUMMARY.get(theme, '')}</p>
        </div>
      </div>
    """)

    put_markdown('# Switch Theme')
    themes = [
        put_image(f"https://cdn.jsdelivr.net/gh/wang0618/PyWebIO@dev/docs/assets/theme/{name}.png").onclick(
            partial(go_app, name=name, new_window=False))
        for name in ALL_THEME if name != theme
    ]
    if info.user_agent.is_mobile:
        put_table([themes[:2], themes[2:]])
    else:
        put_table([themes])

    if theme != 'default':
        put_markdown(f"""
        ### Usage
        Use `pywebio.config()` to apply this theme:
        
        ```python
        @config(theme="{theme}")
        def main():
            put_text("hello world")
        
        start_server(main, port=8080)
        ```
        """)

    put_markdown("""
    ### Credits
    
    The dark theme is modified from ForEvolve's [bootstrap-dark](https://github.com/ForEvolve/bootstrap-dark).
    The sketchy, minty and yeti theme are from [bootswatch](https://bootswatch.com/4/).
    """)

    set_env(input_panel_min_height=100, input_panel_init_height=190)
    output_widgets()
    pin_widgets()
    form()


# bind each theme to the app
main = {
    theme: config(theme=theme, title=f"PyWebIO {theme} theme")(page)
    for theme in ALL_THEME if theme != 'default'
}
main['index'] = page

if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
