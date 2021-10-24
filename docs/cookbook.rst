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

The following code uses the lock mechanism to make the button callback function synchronous:

.. collapse:: Click to expand the code

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

Input in the popup
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. https://github.com/pywebio/PyWebIO/discussions/132

In the following code, we define a ``popup_input()`` function, which can be used to get input in popup:

.. collapse:: Click to expand the code

    .. exportable-codeblock::
        :name: cookbook-redirect-stdout
        :summary: Redirect stdout to PyWebIO

        import threading


        def popup_input(pins, names, title='Please fill out the form'):
            """Show a form in popup window.

            :param list pins: pin output list.
            :param list pins: pin name list.
            :param str title: model title.
            :return: return the form as dict, return None when user cancel the form.
            """
            if not isinstance(pins, list):
                pins = [pins]

            event = threading.Event()
            confirmed_form = None

            def onclick(val):
                nonlocal confirmed_form
                confirmed_form = val
                event.set()

            pins.append(put_buttons([
                {'label': 'Submit', 'value': True},
                {'label': 'Cancel', 'value': False, 'color': 'danger'},
            ], onclick=onclick))
            popup(title=title, content=pins, closable=False)

            event.wait()
            close_popup()
            if not confirmed_form:
                return None

            from pywebio.pin import pin
            return {name: pin[name] for name in names}


        from pywebio.pin import put_input

        result = popup_input([
            put_input('name', label='Input your name'),
            put_input('age', label='Input your age', type="number")
        ], names=['name', 'age'])
        put_text(result)

The code uses :doc:`pin module </pin>` to add input widgets to popup window,
and uses the lock mechanism to wait the form buttons to be clicked.


Redirect stdout to PyWebIO application
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. https://github.com/pywebio/PyWebIO/discussions/21

The following code shows how to redirect stdout of python code and subprocess to PyWebIO application:

.. collapse:: Click to expand the code

    .. exportable-codeblock::
        :name: cookbook-redirect-stdout
        :summary: Redirect stdout to PyWebIO

        import io
        import time
        import subprocess  # ..doc-only
        from contextlib import redirect_stdout

        # redirect `print()` to pywebio
        class WebIO(io.IOBase):
            def write(self, content):
                put_text(content, inline=True)

        with redirect_stdout(WebIO()):
            for i in range(10):
                print(i, time.time())
                time.sleep(0.2)

        ## ----
        import subprocess  # ..demo-only
        # redirect a subprocess' stdout to pywebio
        process = subprocess.Popen("ls -ahl", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                put_text(output.decode('utf8'), inline=True)



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

Cookie and localStorage manipulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. https://github.com/pywebio/PyWebIO/discussions/99

You can use `pywebio.session.run_js()` and `pywebio.session.eval_js()` to deal with cookies or localStorage with js.

``localStorage`` manipulation:

.. exportable-codeblock::
    :name: cookbook-localStorage
    :summary: ``localStorage`` manipulation

    set_localstorage = lambda key, value: run_js("localStorage.setItem(key, value)", key=key, value=value)
    get_localstorage = lambda key: eval_js("localStorage.getItem(key)", key=key)

    set_localstorage('hello', 'world')
    val = get_localstorage('hello')
    put_text(val)


Cookie manipulation:

.. collapse:: Click to expand the code

    .. exportable-codeblock::
        :name: cookbook-cookie
        :summary: Cookie manipulation

        # https://stackoverflow.com/questions/14573223/set-cookie-and-get-cookie-with-javascript
        run_js("""
        window.setCookie = function(name,value,days) {
            var expires = "";
            if (days) {
                var date = new Date();
                date.setTime(date.getTime() + (days*24*60*60*1000));
                expires = "; expires=" + date.toUTCString();
            }
            document.cookie = name + "=" + (value || "")  + expires + "; path=/";
        }
        window.getCookie = function(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }
        """)

        def setcookie(key, value, days=0):
            run_js("setCookie(key, value, days)", key=key, value=value, days=days)

        def getcookie(key):
            return eval_js("getCookie(key)", key=key)

        setcookie('hello', 'world')
        val = getcookie('hello')
        put_text(val)


