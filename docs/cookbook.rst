Cookbook
==========================

.. contents::
   :local:

Interaction related
----------------------------------------------------------------------------------------------

Equivalent to "Press any key to continue"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. exportable-codeblock::
    :name: cookbook-press-anykey-continue
    :summary: Press any key to continue

    actions(buttons=["Continue"])
    put_text("Go next")  # ..demo-only


Output pandas dataframe
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. exportable-codeblock::
    :name: cookbook-pandas-df
    :summary: Output pandas dataframe

    import numpy as np
    import pandas as pd

    df = pd.DataFrame(np.random.randn(6, 4), columns=list("ABCD"))
    put_html(df.to_html(border=0))

.. seealso:: `pandas.DataFrame.to_html — pandas documentation <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_html.html#pandas-dataframe-to-html>`_

Output Matplotlib figure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Simply do not call ``matplotlib.pyplot.show``, directly save the figure to in-memory buffer and output the buffer
via :func:`pywebio.output.put_image`:

.. exportable-codeblock::
    :name: cookbook-matplotlib
    :summary: Output Matplotlib plot

    import matplotlib
    import matplotlib.pyplot as plt
    import io
    import pywebio

    matplotlib.use('agg')  # required, use a non-interactive backend

    fig, ax = plt.subplots()  # Create a figure containing a single axes.
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])  # Plot some data on the axes.

    buf = io.BytesIO()
    fig.savefig(buf)
    pywebio.output.put_image(buf.getvalue())

The ``matplotlib.use('agg')`` is required so that the server does not try to create (and then destroy) GUI windows
that will never be seen.

When using Matplotlib in a web server (multiple threads environment), pyplot may cause some conflicts in some cases,
read the following articles for more information:

    * `Multi Threading in Python and Pyplot | by Ranjitha Korrapati | Medium <https://medium.com/@ranjitha.korrapati/multi-threading-in-python-and-pyplot-46f325e6a9d0>`_

    * `Embedding in a web application server (Flask) — Matplotlib documentation <https://matplotlib.org/stable/gallery/user_interfaces/web_application_server_sgskip.html>`_


Blocking confirm model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. collapse:: Code

    .. exportable-codeblock::
        :name: cookbook-confirm-model
        :summary: Blocking confirm model

        import threading
        from pywebio import output

        def confirm(title, content=None, timeout=None):
            """Show a confirm model.

            :param str title: Model title.
            :param list/put_xxx() content: Model content.
            :param None/float timeout: Seconds for operation time out.
            :return: Return `True` when the "CONFIRM" button is clicked,
                return `False` when the "CANCEL" button is clicked,
                return `None` when a timeout is given and the operation times out.
            """
            if not isinstance(content, list):
                content = [content]

            event = threading.Event()
            result = None

            def onclick(val):
                nonlocal result
                result = val
                event.set()

            content.append(output.put_buttons([
                {'label': 'CONFIRM', 'value': True},
                {'label': 'CANCEL', 'value': False, 'color': 'danger'},
            ], onclick=onclick))
            output.popup(title=title, content=content, closable=False)

            event.wait(timeout=timeout)  # wait the model buttons are clicked
            output.close_popup()
            return result


        res = confirm('Confirm', 'You have 5 seconds to make s choice', timeout=5)
        output.put_text("Your choice is:", res)



Web application related
----------------------------------------------------------------------------------------------

Get URL parameters of current page
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use URL parameter (known also as "query strings" or "URL query parameters") to pass information to your web
application. In PyWebIO application, you can use the following code to get the URL parameters as a Python dict.

.. exportable-codeblock::
    :name: cookbook-url-query
    :summary: Get URL parameters of current page

    # `query` is a dict
    query = eval_js("Object.fromEntries(new URLSearchParams(window.location.search))")
    put_text(query)


Add Google AdSense/Analytics code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you setup Google AdSense/Analytics, you will get a javascript file and a piece of code that needs to be inserted
into your application page, you can use :func:`pywebio.config()` to inject js file and code to your PyWebIO application::

    from pywebio import start_server, output, config

    js_file = "https://www.googletagmanager.com/gtag/js?id=G-xxxxxxx"
    js_code = """
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());

    gtag('config', 'G-xxxxxxx');
    """

    @config(js_file=js_file, js_code=js_code)
    def main():
        output.put_text("hello world")

    start_server(main, port=8080)


Refresh page on connection lost
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Add the following code to the beginning of your PyWebIO application main function::

    session.run_js('WebIO._state.CurrentSession.on_session_close(()=>{setTimeout(()=>location.reload(), 4000})')

