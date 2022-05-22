"""
``pywebio.pin`` --- Persistent input
===========================================================================

*pin == Persistent input == Pinning input widget to the page*

Overview
------------------

As you already know, the input function of PyWebIO is blocking
and the input form will be destroyed after successful submission.
In most cases, it enough to use this way to get input.
However in some cases, you may want to make the input form **not** disappear after submission,
and can continue to receive input.

So PyWebIO provides the ``pin`` module to achieve persistent input by pinning input widgets to the page.

The ``pin`` module achieves persistent input in 3 parts:

First, this module provides some pin widgets.
Pin widgets are not different from output widgets in ``pywebio.output`` module,
besides that they can also receive input.

This code outputs an text input pin widget:

.. exportable-codeblock::
    :name: pin-put_input
    :summary: `put_input()` example

    put_input('input', label='This is a input widget')

In fact, the usage of pin widget function is same as the output function.
You can use it as part of the combined output, or you can output pin widget to a scope:

.. exportable-codeblock::
    :name: pin-basic
    :summary: Pin widget as output function

    put_row([
        put_input('input'),
        put_select('select', options=['A', 'B', 'C'])
    ])

    with use_scope('search-area'):
        put_input('search', placeholder='Search')

Then, you can use the `pin` object to get the value of pin widget:

.. exportable-codeblock::
    :name: get-pin-value
    :summary: Use the `pin` object to get the value of pin widget

    put_input('pin_name')
    put_buttons(['Get Pin Value'], lambda _: put_text(pin.pin_name))

The first parameter that the pin widget function receives is the name of the pin widget.
You can get the current value of the pin widget via the attribute of the same name of the `pin` object.

In addition, the `pin` object also supports getting the value of the pin widget by index, that is to say::

    pin['pin_name'] == pin.pin_name

There are also two useful functions when you use the pin module: `pin_wait_change()` and `pin_update()`.

Since the pin widget functions is not blocking,
`pin_wait_change()` is used to wait for the value of one of a list of pin widget to change, it 's a blocking function.

`pin_update()` can be used to update attributes of pin widgets.

Pin widgets
------------------
Each pin widget function corresponds to an input function of :doc:`input <./input>` module.
(For performance reasons, no pin widget for `file_upload() <pywebio.input.file_upload>` input function)

The function of pin widget supports most of the parameters of the corresponding input function.
Here lists the difference between the two in parameters:

 * The first parameter of pin widget function is always the name of the widget,
   and if you output two pin widgets with the same name, the previous one will expire.
 * Pin functions don't support the ``on_change`` and ``validate`` callbacks, and the ``required`` parameter.
   (There is a :func:`pin_on_change()` function as an alternative to ``on_change``)
 * Pin functions have additional ``scope`` and ``position`` parameters for output control.

.. autofunction:: put_input
.. autofunction:: put_textarea
.. autofunction:: put_select
.. autofunction:: put_checkbox
.. autofunction:: put_radio
.. autofunction:: put_slider
.. autofunction:: put_actions

Pin utils
------------------
.. data:: pin

    Pin widgets value getter and setter.

    You can use attribute or key index of ``pin`` object to get the current value of a pin widget.
    By default, when accessing the value of a widget that does not exist, it returns ``None`` instead of
    throwing an exception.

    You can also use the ``pin`` object to set the value of pin widget:

    .. exportable-codeblock::
        :name: set-pin-value
        :summary: Use the `pin` object to set the value of pin widget

        import time  # ..demo-only
        put_input('counter', type='number', value=0)

        while True:
            pin.counter = pin.counter + 1  # Equivalent to: pin['counter'] = pin['counter'] + 1
            time.sleep(1)

    Note: When using :ref:`coroutine-based session <coroutine_based_session>`,
    you need to use the ``await pin.name`` (or ``await pin['name']``) syntax to get pin widget value.

    Use `pin.pin.use_strict()` to enable strict mode for getting pin widget value.
    An ``AssertionError`` will be raised when try to get value of pin widgets that are currently not in the page.

.. autofunction:: pin_wait_change
.. autofunction:: pin_update
.. autofunction:: pin_on_change

"""

import string

from pywebio.input import parse_input_update_spec
from pywebio.output import OutputPosition, Output
from pywebio.output import _get_output_spec
from .io_ctrl import send_msg, single_input_kwargs, output_register_callback
from .session import next_client_event, chose_impl
from .utils import check_dom_name_value

_pin_name_chars = set(string.ascii_letters + string.digits + '_-')

__all__ = ['put_input', 'put_textarea', 'put_select', 'put_checkbox', 'put_radio', 'put_slider', 'put_actions',
           'pin', 'pin_update', 'pin_wait_change', 'pin_on_change']


def _pin_output(single_input_return, scope, position):
    input_kwargs = single_input_kwargs(single_input_return)
    spec = _get_output_spec('pin', input=input_kwargs['item_spec'], scope=scope, position=position)
    return Output(spec)


def put_input(name, type='text', *, label='', value=None, placeholder=None, readonly=None, datalist=None,
              help_text=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output an input widget. Refer to: `pywebio.input.input()`"""
    from pywebio.input import input
    check_dom_name_value(name, 'pin `name`')
    single_input_return = input(name=name, label=label, value=value, type=type, placeholder=placeholder,
                                readonly=readonly, datalist=datalist, help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_textarea(name, *, label='', rows=6, code=None, maxlength=None, minlength=None, value=None, placeholder=None,
                 readonly=None, help_text=None, scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a textarea widget. Refer to: `pywebio.input.textarea()`"""
    from pywebio.input import textarea
    check_dom_name_value(name, 'pin `name`')
    single_input_return = textarea(
        name=name, label=label, rows=rows, code=code, maxlength=maxlength,
        minlength=minlength, value=value, placeholder=placeholder, readonly=readonly, help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_select(name, options=None, *, label='', multiple=None, value=None, help_text=None,
               scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a select widget. Refer to: `pywebio.input.select()`"""
    from pywebio.input import select
    check_dom_name_value(name, 'pin `name`')
    single_input_return = select(name=name, options=options, label=label, multiple=multiple,
                                 value=value, help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_checkbox(name, options=None, *, label='', inline=None, value=None, help_text=None,
                 scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a checkbox widget. Refer to: `pywebio.input.checkbox()`"""
    from pywebio.input import checkbox
    check_dom_name_value(name, 'pin `name`')
    single_input_return = checkbox(name=name, options=options, label=label, inline=inline, value=value,
                                   help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_radio(name, options=None, *, label='', inline=None, value=None, help_text=None,
              scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a radio widget. Refer to: `pywebio.input.radio()`"""
    from pywebio.input import radio
    check_dom_name_value(name, 'pin `name`')
    single_input_return = radio(name=name, options=options, label=label, inline=inline, value=value,
                                help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_slider(name, *, label='', value=0, min_value=0, max_value=100, step=1, required=None, help_text=None,
               scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a slide widget. Refer to: `pywebio.input.slider()`"""
    from pywebio.input import slider
    check_dom_name_value(name, 'pin `name`')
    single_input_return = slider(name=name, label=label, value=value, min_value=min_value, max_value=max_value,
                                 step=step, required=required, help_text=help_text)
    return _pin_output(single_input_return, scope, position)


def put_actions(name, *, label='', buttons=None, help_text=None,
                scope=None, position=OutputPosition.BOTTOM) -> Output:
    """Output a group of action button. Refer to: `pywebio.input.actions()`

    Unlike the ``actions()``, ``put_actions()`` won't submit any form, it will only set the value of the pin widget.
    Only 'submit' type button is available in pin widget version.

    .. versionadded:: 1.4
    """
    from pywebio.input import actions
    check_dom_name_value(name, 'pin `name`')
    single_input_return = actions(name=name, label=label, buttons=buttons, help_text=help_text)
    input_kwargs = single_input_kwargs(single_input_return)
    for btn in input_kwargs['item_spec']['buttons']:
        assert btn['type'] == 'submit', "The `put_actions()` pin widget only accept 'submit' type button."
    return _pin_output(input_kwargs, scope, position)


@chose_impl
def get_client_val():
    res = yield next_client_event()
    assert res['event'] == 'js_yield', "Internal Error, please report this bug on " \
                                       "https://github.com/wang0618/PyWebIO/issues"
    return res['data']


@chose_impl
def get_pin_value(name, strict):
    send_msg('pin_value', spec=dict(name=name))
    data = yield get_client_val()
    assert not strict or data, 'pin widget "%s" doesn\'t exist.' % name
    return (data or {}).get('value')


class Pin_:
    _strict = False

    def use_strict(self):
        """
        Enable strict mode for getting pin widget value.
        An AssertionError will be raised when try to get value of pin widgets that are currently not in the page.
        """
        object.__setattr__(self, '_strict', True)

    def __getattr__(self, name):
        """__getattr__ is only invoked if the attribute wasn't found the usual ways"""
        if name.startswith('__'):
            raise AttributeError('Pin object has no attribute %r' % name)
        return self.__getitem__(name)

    def __getitem__(self, name):
        check_dom_name_value(name, 'pin `name`')
        return get_pin_value(name, self._strict)

    def __setattr__(self, name, value):
        """
        __setattr__ will be invoked regardless of whether the attribute be found
        """
        assert name != 'use_strict', "'use_strict' is a reserve name, can't use as pin widget name"
        check_dom_name_value(name, 'pin `name`')
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        send_msg('pin_update', spec=dict(name=name, attributes={"value": value}))


# pin widgets value getter (and setter).
pin = Pin_()


def pin_wait_change(*names, timeout=None):
    """``pin_wait_change()`` listens to a list of pin widgets, when the value of any widgets changes,
    the function returns with the name and value of the changed widget.

    :param str names: List of names of pin widget
    :param int/None timeout: If ``timeout`` is a positive number, ``pin_wait_change()`` blocks at most ``timeout`` seconds
        and returns ``None`` if no changes to the widgets within that time. Set to ``None`` (the default) to disable timeout.
    :return dict/None: ``{"name": name of the changed widget, "value": current value of the changed widget }`` ,
        when a timeout occurs, return ``None``.

    Example:

    .. exportable-codeblock::
        :name: pin_wait_change
        :summary: `pin_wait_change()` example

        put_input('a', type='number', value=0)
        put_input('b', type='number', value=0)

        while True:
            changed = pin_wait_change('a', 'b')
            with use_scope('res', clear=True):
                put_code(changed)
                put_text("a + b = %s" % (pin.a + pin.b))

    :demo_host:`Here </markdown_previewer>` is an demo of using `pin_wait_change()` to make a markdown previewer.

    Note that: updating value with the :data:`pin` object or `pin_update()`
    does not trigger `pin_wait_change()` to return.

    When using :ref:`coroutine-based session <coroutine_based_session>`,
    you need to use the ``await pin_wait_change()`` syntax to invoke this function.
    """
    assert len(names) >= 1, "`names` can't be empty."
    if len(names) == 1 and isinstance(names[0], (list, tuple)):
        names = names[0]

    send_msg('pin_wait', spec=dict(names=names, timeout=timeout))

    return get_client_val()


def pin_update(name, **spec):
    """Update attributes of pin widgets.

    :param str name: The ``name`` of the target input widget.
    :param spec: The pin widget parameters need to be updated.
       Note that those parameters can not be updated: ``type``, ``name``, ``code``, ``multiple``
    """
    check_dom_name_value(name, 'pin `name`')
    attributes = parse_input_update_spec(spec)
    send_msg('pin_update', spec=dict(name=name, attributes=attributes))


def pin_on_change(name, onchange=None, clear=False, init_run=False, **callback_options):
    """
    Bind a callback function to pin widget, the function will be called when user change the value of the pin widget.

    The ``onchange`` callback is invoked with one argument, the changed value of the pin widget.
    You can bind multiple functions to one pin widget, those functions will be invoked sequentially
    (default behavior, can be changed by `clear` parameter).

    :param str name: pin widget name
    :param callable onchange: callback function
    :param bool clear: whether to clear the previous callbacks bound to this pin widget.
       If you just want to clear callbacks and not set new callback, use ``pin_on_change(name, clear=True)``.
    :param bool init_run: whether to run the ``onchange`` callback once immediately before the pin widget changed.
       This parameter can be used to initialize the output.
    :param callback_options: Other options of the ``onclick`` callback.
       Refer to the ``callback_options`` parameter of :func:`put_buttons() <pywebio.output.put_buttons>`

    .. versionadded:: 1.6
    """
    assert not (onchange is None and clear is False), "When `onchange` is `None`, `clear` must be `True`"
    if onchange is not None:
        callback_id = output_register_callback(onchange, **callback_options)
        if init_run:
            onchange(pin[name])
    else:
        callback_id = None
    send_msg('pin_onchange', spec=dict(name=name, callback_id=callback_id, clear=clear))
