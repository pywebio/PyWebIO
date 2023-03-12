"""

This module provides functions to get all kinds of input of user from the browser

There are two ways to use the input functions, one is to call the input function alone to get a single input::

    name = input("What's your name")
    print("Your name is %s" % name)

The other is to use `input_group` to get multiple inputs at once::

    info = input_group("User info",[
      input('Input your name', name='name'),
      input('Input your age', name='age', type=NUMBER)
    ])
    print(info['name'], info['age'])

When use `input_group`, you needs to provide the ``name`` parameter in each input function to identify the input items in the result.

.. note::

   PyWebIO determines whether the input function is in `input_group` or is called alone according to whether the
   ``name`` parameter is passed. So when calling an input function alone, **do not** set the ``name`` parameter;
   when calling the input function in `input_group`, you **must** provide the ``name`` parameter.

By default, the user can submit empty input value. If the user must provide a non-empty input value, you need to
pass ``required=True`` to the input function (some input functions do not support the ``required`` parameter)

The input functions in this module is blocking, and the input form will be destroyed after successful submission.
If you want the form to always be displayed on the page and receive input continuously,
you can consider the :doc:`pin <./pin>` module.

Functions list
-----------------

.. list-table::

   * - Function name
     - Description

   * - `input <pywebio.input.input>`
     - Text input

   * - `textarea <pywebio.input.textarea>`
     - Multi-line text input

   * - `select <pywebio.input.select>`
     - Drop-down selection

   * - `checkbox <pywebio.input.checkbox>`
     - Checkbox

   * - `radio <pywebio.input.radio>`
     - Radio

   * - `slider <pywebio.input.slider>`
     - Slider

   * - `actions <pywebio.input.actions>`
     - Actions selection

   * - `file_upload <pywebio.input.file_upload>`
     - File uploading

   * - `input_group <pywebio.input.input_group>`
     - Input group

   * - `input_update <pywebio.input.input_update>`
     - Update input item


Functions doc
--------------
"""
import copy
import logging
import os.path
from collections.abc import Mapping
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .io_ctrl import input_control, output_register_callback, send_msg, single_input, single_input_kwargs
from .platform import page as platform_setting
from .session import get_current_session, get_current_task_id
from .utils import Setter, check_dom_name_value, parse_file_size

logger = logging.getLogger(__name__)

TEXT = 'text'
NUMBER = "number"
FLOAT = "float"
PASSWORD = "password"
URL = "url"
DATE = "date"
TIME = "time"
COLOR = "color"
DATETIME_LOCAL = "datetime-local"
DATETIME = DATETIME_LOCAL

CHECKBOX = 'checkbox'
RADIO = 'radio'
SELECT = 'select'
TEXTAREA = 'textarea'

__all__ = ['TEXT', 'NUMBER', 'FLOAT', 'PASSWORD', 'URL', 'DATE',
           'TIME', 'COLOR', 'DATETIME_LOCAL', 'DATETIME', 'input', 'textarea',
           'select', 'checkbox', 'radio', 'actions', 'file_upload',
           'slider', 'input_group', 'input_update']


def _parse_args(kwargs, excludes=()):
    """parse the raw parameters that pass to input functions

     - excludes: the parameters that don't appear in returned spec
     - remove the parameters whose value is None

    :return:（spec，valid_func）
    """
    kwargs = {k: v for k, v in kwargs.items() if v is not None and k not in excludes}
    check_dom_name_value(kwargs.get('name', ''), '`name`')

    kwargs.update(kwargs.get('other_html_attrs', {}))
    kwargs.pop('other_html_attrs', None)

    if kwargs.get('validate'):
        kwargs['onblur'] = True
    valid_func = kwargs.pop('validate', lambda _: None)

    if kwargs.get('onchange'):
        onchange_func = kwargs['onchange']
        kwargs['onchange'] = True
    else:
        onchange_func = lambda _: None

    return kwargs, valid_func, onchange_func


def input(label: str = '', type: str = TEXT, *, validate: Callable[[Any], Optional[str]] = None, name: str = None,
          value: Union[str, int] = None,
          action: Tuple[str, Callable[[Callable], None]] = None, onchange: Callable[[Any], None] = None,
          placeholder: str = None, required: bool = None,
          readonly: bool = None, datalist: List[str] = None, help_text: str = None, **other_html_attrs):
    r"""Text input

    :param str label: Label of input field.
    :param str type: Input type. Currently, supported types are：`TEXT` , `NUMBER` , `FLOAT` , `PASSWORD` , `URL` , `DATE` , `TIME`, `DATETIME`, `COLOR`

       The value of `DATE` , `TIME`, `DATETIME` type is a string in the format of `YYYY-MM-DD` , `HH:MM:SS` , `YYYY-MM-DDTHH:MM` respectively
       (`%Y-%m-%d`, `%H:%M:%S`, `%Y-%m-%dT%H:%M` in python `strptime() <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`_ format).
    :param callable validate: Input value validation function. If provided, the validation function will be called when
        user completes the input field or submits the form.

        ``validate`` receives the input value as a parameter. When the input value is valid, it returns ``None``.
        When the input value is invalid, it returns an error message string.

        For example:

        .. exportable-codeblock::
            :name: input-valid-func
            :summary: `input()` validation

            def check_age(age):
                if age>30:
                    return 'Too old'
                elif age<10:
                    return 'Too young'
            input('Input your age', type=NUMBER, validate=check_age)

    :param str name: A string specifying a name for the input. Used with `input_group()` to identify different input
        items in the results of the input group. If call the input function alone, this parameter can **not** be set!
    :param str value: The initial value of the input
    :type action: tuple(label:str, callback:callable)
    :param action: Put a button on the right side of the input field, and user can click the button to set the value for the input.

        ``label`` is the label of the button, and ``callback`` is the callback function to set the input value when clicked.

        The callback is invoked with one argument, the ``set_value``. ``set_value`` is a callable object, which is
        invoked with one or two arguments. You can use ``set_value`` to set the value for the input.

        ``set_value`` can be invoked with one argument: ``set_value(value:str)``. The ``value`` parameter is the value to be set for the input.

        ``set_value`` can be invoked with two arguments: ``set_value(value:any, label:str)``. Each arguments are described as follows:

         * ``value`` : The real value of the input, can be any object. it will not be passed to the user browser.
         * ``label`` : The text displayed to the user

        When calling ``set_value`` with two arguments, the input item in web page will become read-only.

        The usage scenario of ``set_value(value:any, label:str)`` is: You need to dynamically generate the value of the
        input in the callback, and hope that the result displayed to the user is different from the actual submitted data
        (for example, result displayed to the user can be some user-friendly texts, and the value of the input can be
        objects that are easier to process)

        Usage example:

        .. exportable-codeblock::
            :name: input-action
            :summary: `input()` action usage

            import time
            def set_now_ts(set_value):
                set_value(int(time.time()))

            ts = input('Timestamp', type=NUMBER, action=('Now', set_now_ts))
            put_text('Timestamp:', ts)  # ..demo-only
            ## ----
            from datetime import date,timedelta
            def select_date(set_value):
                with popup('Select Date'):
                    put_buttons(['Today'], onclick=[lambda: set_value(date.today(), 'Today')])
                    put_buttons(['Yesterday'], onclick=[lambda: set_value(date.today() - timedelta(days=1), 'Yesterday')])

            d = input('Date', action=('Select', select_date), readonly=True)
            put_text(type(d), d)

        Note: When using :ref:`Coroutine-based session <coroutine_based_session>` implementation, the ``callback``
        function can be a coroutine function.

    :param callable onchange: A callback function which will be called when user change the value of this input field.

       The ``onchange`` callback is invoked with one argument, the current value of input field.
       A typical usage scenario of ``onchange`` is to update other input item by using `input_update()`

    :param str placeholder: A hint to the user of what can be entered in the input. It will appear in the input field when it has no value set.
    :param bool required: Whether a value is required for the input to be submittable, default is ``False``
    :param bool readonly: Whether the value is readonly(not editable)
    :param list datalist: A list of predefined values to suggest to the user for this input. Can only be used when ``type=TEXT``
    :param str help_text: Help text for the input. The text will be displayed below the input field with small font
    :param other_html_attrs: Additional html attributes added to the input element.
        reference: https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/input#%E5%B1%9E%E6%80%A7
    :return: The value that user input.
    """

    item_spec, valid_func, onchange_func = _parse_args(locals(), excludes=('action',))

    # check input type
    allowed_type = {TEXT, NUMBER, FLOAT, PASSWORD, URL, DATE, TIME, COLOR, DATETIME_LOCAL}
    assert type in allowed_type, 'Input type not allowed.'

    value_setter = None
    if action:
        label, callback = action
        task_id = get_current_task_id()

        value_setter = Setter()

        def _set_value(value, label=value_setter):
            spec = {
                'target_name': item_spec.get('name', 'data'),
                'attributes': {'value': value}
            }
            if label is not value_setter:
                value_setter.label = label
                spec['attributes']['value'] = label
                spec['attributes']['readonly'] = True
            value_setter.value = value
            msg = dict(command='update_input', task_id=task_id, spec=spec)
            get_current_session().send_task_command(msg)

        callback_id = output_register_callback(lambda _: callback(_set_value))
        item_spec['action'] = dict(label=label, callback_id=callback_id)

    def preprocess_func(d):  # Convert the original data submitted by the user
        if value_setter is not None and value_setter.label == d:
            return value_setter.value

        return d

    return single_input(item_spec, valid_func, preprocess_func, onchange_func)


def textarea(label: str = '', *, rows: int = 6, code: Union[bool, Dict] = None, maxlength: int = None,
             minlength: int = None,
             validate: Callable[[Any], Optional[str]] = None, name: str = None, value: str = None,
             onchange: Callable[[Any], None] = None,
             placeholder: str = None, required: bool = None, readonly: bool = None, help_text: str = None,
             **other_html_attrs):
    r"""Text input area (multi-line text input)

    :param int rows: The number of visible text lines for the input area. Scroll bar will be used when content exceeds.
    :param int maxlength: The maximum number of characters (UTF-16 code units) that the user can enter.
        If this value isn't specified, the user can enter an unlimited number of characters.
    :param int minlength: The minimum number of characters (UTF-16 code units) required that the user should enter.
    :param dict/bool code: Enable a code style editor by providing the `Codemirror <https://codemirror.net/>`_ options:

        .. exportable-codeblock::
            :name: textarea-code
            :summary: `textarea()` code editor style

            res = textarea('Text area', code={
                'mode': "python",
                'theme': 'darcula'
            })
            put_code(res, language='python')  # ..demo-only

        You can simply use ``code={}`` or ``code=True`` to enable code style editor.
        You can use ``Esc`` or ``F11`` to toggle fullscreen of code style textarea.

        Some commonly used Codemirror options are listed :ref:`here <codemirror_options>`.

    :param - label, validate, name, value, onchange, placeholder, required, readonly, help_text, other_html_attrs:
        Those arguments have the same meaning as for `input()`
    :return: The string value that user input.
    """
    item_spec, valid_func, onchange_func = _parse_args(locals())
    item_spec['type'] = TEXTAREA

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def _parse_select_options(options):
    # Convert the `options` parameter in the `select`, `checkbox`, and `radio` functions to a unified format
    # Available forms of option:
    # {value:, label:, [selected:,] [disabled:]}
    # (value, label, [selected,] [disabled])
    # value (label same as value)
    opts_res = []
    for opt in options:
        opt = copy.deepcopy(opt)
        if isinstance(opt, Mapping):
            assert 'value' in opt and 'label' in opt, 'options item must have value and label key'
        elif isinstance(opt, (list, tuple)):
            assert len(opt) > 1 and len(opt) <= 4, 'options item format error'
            opt = dict(zip(('label', 'value', 'selected', 'disabled'), opt))
        else:
            opt = dict(value=opt, label=opt)
        opts_res.append(opt)

    return opts_res


def _set_options_selected(options, value):
    """set `selected` attribute for `options`"""
    if not isinstance(value, (list, tuple)):
        value = [value]
    for opt in options:
        if opt['value'] in value:
            opt['selected'] = True
    return options


def select(label: str = '', options: List[Union[Dict[str, Any], Tuple, List, str]] = None, *, multiple: bool = None,
           validate: Callable[[Any], Optional[str]] = None, name: str = None, value: Union[List, str] = None,
           onchange: Callable[[Any], None] = None, native: bool = True, required: bool = None, help_text: str = None,
           **other_html_attrs):
    r"""Drop-down selection

    By default, only one option can be selected at a time, you can set ``multiple`` parameter to enable multiple selection.

    :param list options: list of options. The available formats of the list items are:

        * dict::

            {
                "label":(str) option label,
                "value":(object) option value,
                "selected":(bool, optional) whether the option is initially selected,
                "disabled":(bool, optional) whether the option is initially disabled
            }

        * tuple or list: ``(label, value, [selected,] [disabled])``
        * single value: label and value of option use the same value

        Attention：

        1. The ``value`` of option can be any JSON serializable object
        2. If the ``multiple`` is not ``True``, the list of options can only have one ``selected`` item at most.

    :param bool multiple: whether multiple options can be selected
    :param value: The value of the initial selected item. When ``multiple=True``, ``value`` must be a list.
       You can also set the initial selected option by setting the ``selected`` field in the ``options`` list item.
    :type value: list or str
    :param bool required: Whether to select at least one item, only available when ``multiple=True``
    :param bool native: Using browser's native select component rather than
        `bootstrap-select <https://github.com/snapappointments/bootstrap-select>`_. This is the default behavior.
    :param - label, validate, name, onchange, help_text, other_html_attrs: Those arguments have the same meaning as for `input()`
    :return: If ``multiple=True``, return a list of the values in the ``options`` selected by the user;
        otherwise, return the single value selected by the user.
    """
    assert options is not None, 'Required `options` parameter in select()'

    item_spec, valid_func, onchange_func = _parse_args(locals(), excludes=['value'])
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        item_spec['options'] = _set_options_selected(item_spec['options'], value)
    item_spec['type'] = SELECT

    return single_input(item_spec, valid_func=valid_func, preprocess_func=lambda d: d, onchange_func=onchange_func)


def checkbox(label: str = '', options: List[Union[Dict[str, Any], Tuple, List, str]] = None, *, inline: bool = None,
             validate: Callable[[Any], Optional[str]] = None,
             name: str = None, value: List = None, onchange: Callable[[Any], None] = None, help_text: str = None,
             **other_html_attrs):
    r"""A group of check box that allowing single values to be selected/deselected.

    :param list options: List of options. The format is the same as the ``options`` parameter of the `select()` function
    :param bool inline: Whether to display the options on one line. Default is ``False``
    :param list value: The value list of the initial selected items.
       You can also set the initial selected option by setting the ``selected`` field in the ``options`` list item.
    :param - label, validate, name, onchange, help_text, other_html_attrs: Those arguments have the same meaning as for `input()`
    :return: A list of the values in the ``options`` selected by the user
    """
    assert options is not None, 'Required `options` parameter in checkbox()'

    item_spec, valid_func, onchange_func = _parse_args(locals(), excludes=['value'])
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        item_spec['options'] = _set_options_selected(item_spec['options'], value)
    item_spec['type'] = CHECKBOX

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def radio(label: str = '', options: List[Union[Dict[str, Any], Tuple, List, str]] = None, *, inline: bool = None,
          validate: Callable[[Any], Optional[str]] = None,
          name: str = None, value: str = None, onchange: Callable[[Any], None] = None, required: bool = None,
          help_text: str = None, **other_html_attrs):
    r"""A group of radio button. Only a single button can be selected.

    :param list options: List of options. The format is the same as the ``options`` parameter of the `select()` function
    :param bool inline: Whether to display the options on one line. Default is ``False``
    :param str value: The value of the initial selected items.
       You can also set the initial selected option by setting the ``selected`` field in the ``options`` list item.
    :param bool required: whether to must select one option. (the user can select nothing option by default)
    :param - label, validate, name, onchange, help_text, other_html_attrs: Those arguments have the same meaning as for `input()`
    :return: The value of the option selected by the user, if the user does not select any value, return ``None``
    """
    assert options is not None, 'Required `options` parameter in radio()'

    item_spec, valid_func, onchange_func = _parse_args(locals())
    item_spec['options'] = _parse_select_options(options)
    if value is not None:
        del item_spec['value']
        item_spec['options'] = _set_options_selected(item_spec['options'], value)

    # From https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/required
    # In the case of a same named group of radio buttons, if a single radio button in the group has the required attribute,
    # a radio button in that group must be checked, although it doesn't have to be the one with the attribute is applied
    if required is not None:
        del item_spec['required']
        item_spec['options'][-1]['required'] = required
    item_spec['type'] = RADIO

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def _parse_action_buttons(buttons):
    """
    :param label:
    :param actions: action list
        action available format：

        * dict: ``{label:button label, value:button value, [type: button type], [disabled:is disabled?]}``
        * tuple or list: ``(label, value, [type], [disabled])``
        * single value: label and value of button share the same value

    :return: dict format
    """
    act_res = []
    for act in buttons:
        act = copy.deepcopy(act)
        if isinstance(act, Mapping):
            assert 'label' in act, 'actions item must have label key'
            assert 'value' in act or act.get('type', 'submit') != 'submit' or act.get('disabled'), \
                'actions item must have value key for submit type'
        elif isinstance(act, (list, tuple)):
            assert len(act) in (2, 3, 4), 'actions item format error'
            act = dict(zip(('label', 'value', 'type', 'disabled'), act))
        else:
            act = dict(value=act, label=act)

        act.setdefault('type', 'submit')
        assert act['type'] in ('submit', 'reset', 'cancel'), \
            "submit type must be 'submit'/'reset'/'cancel', not %r" % act['type']
        act_res.append(act)

    return act_res


def actions(label: str = '', buttons: List[Union[Dict[str, Any], Tuple, List, str]] = None, name: str = None,
            help_text: str = None):
    r"""Actions selection

    It is displayed as a group of buttons on the page. After the user clicks the button of it,
    it will behave differently depending on the type of the button.

    :param list buttons: list of buttons. The available formats of the list items are:

        * dict::

             {
                "label":(str) button label,
                "value":(object) button value,
                "type":(str, optional) button type,
                "disabled":(bool, optional) whether the button is disabled,
                "color":(str, optional) button color
             }

          When ``type='reset'/'cancel'`` or ``disabled=True``, ``value`` can be omitted
        * tuple or list: ``(label, value, [type], [disabled])``
        * single value: label and value of button use the same value

       The ``value`` of button can be any JSON serializable object.

       ``type`` can be:

        * ``'submit'`` : After clicking the button, the entire form is submitted immediately,
          and the value of this input item in the final form is the ``value`` of the button that was clicked.
          ``'submit'`` is the default value of ``type``
        * ``'cancel'`` : Cancel form. After clicking the button, the entire form will be submitted immediately,
          and the form value will return ``None``
        * ``'reset'`` : Reset form. After clicking the button, the entire form will be reset,
          and the input items will become the initial state.
          Note: After clicking the ``type=reset`` button, the form will not be submitted,
          and the ``actions()`` call will not return

        The ``color`` of button can be one of: `primary`, `secondary`, `success`, `danger`, `warning`, `info`, `light`,
        `dark`.

    :param - label, name, help_text: Those arguments have the same meaning as for `input()`
    :return: If the user clicks the ``type=submit`` button to submit the form,
        return the value of the button clicked by the user.
        If the user clicks the ``type=cancel`` button or submits the form by other means, ``None`` is returned.

    When ``actions()`` is used as the last input item in `input_group()` and contains a button with ``type='submit'``,
    the default submit button of the `input_group()` form will be replace with the current ``actions()``

    **usage scenes of actions() **

    .. _custom_form_ctrl_btn:

    * Perform simple selection operations:

    .. exportable-codeblock::
        :name: actions-select
        :summary: Use `actions()` to perform simple selection

        confirm = actions('Confirm to delete file?', ['confirm', 'cancel'],
                              help_text='Unrecoverable after file deletion')
        if confirm=='confirm':  # ..doc-only
            ...  # ..doc-only
        put_markdown('You clicked the `%s` button' % confirm)  # ..demo-only

    Compared with other input items, when using `actions()`, the user only needs to click once to complete the submission.

    * Replace the default submit button:

    .. exportable-codeblock::
        :name: actions-submit
        :summary: Use `actions()` to replace the default submit button

        import json  # ..demo-only
                     # ..demo-only
        info = input_group('Add user', [
            input('username', type=TEXT, name='username', required=True),
            input('password', type=PASSWORD, name='password', required=True),
            actions('actions', [
                {'label': 'Save', 'value': 'save'},
                {'label': 'Save and add next', 'value': 'save_and_continue'},
                {'label': 'Reset', 'type': 'reset', 'color': 'warning'},
                {'label': 'Cancel', 'type': 'cancel', 'color': 'danger'},
            ], name='action', help_text='actions'),
        ])
        put_code('info = ' + json.dumps(info, indent=4))
        if info is not None:
            save_user(info['username'], info['password'])  # ..doc-only
            if info['action'] == 'save_and_continue':
                add_next()  # ..doc-only
                put_text('Save and add next...')  # ..demo-only

    """
    assert buttons is not None, 'Required `buttons` parameter in actions()'

    item_spec, valid_func, onchange_func = _parse_args(locals())
    item_spec['type'] = 'actions'
    item_spec['buttons'] = _parse_action_buttons(buttons)

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def file_upload(label: str = '', accept: Union[List, str] = None, name: str = None, placeholder: str = 'Choose file',
                multiple: bool = False, max_size: Union[int, str] = 0, max_total_size: Union[int, str] = 0,
                required: bool = None, help_text: str = None, **other_html_attrs):
    r"""File uploading

    :param accept: Single value or list, indicating acceptable file types. The available formats of file types are:

        * A valid case-insensitive filename extension, starting with a period (".") character. For example: ``.jpg``, ``.pdf``, or ``.doc``.
        * A valid MIME type string, with no extensions.
          For examples: ``application/pdf``, ``audio/*``, ``video/*``, ``image/*``.
          For more information, please visit: https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types

    :type accept: str or list
    :param str placeholder: A hint to the user of what to be uploaded. It will appear in the input field when there is no file selected.
    :param bool multiple: Whether to allow upload multiple files. Default is ``False``.
    :param int/str max_size: The maximum size of a single file, exceeding the limit will prohibit uploading.
        The default is 0, which means there is no limit to the size.

       ``max_size`` can be a integer indicating the number of bytes, or a case-insensitive string ending with `K` / `M` / `G`
       (representing kilobytes, megabytes, and gigabytes, respectively).
       E.g: ``max_size=500``, ``max_size='40K'``, ``max_size='3M'``

    :param int/str max_total_size: The maximum size of all files. Only available when ``multiple=True``.
        The default is 0, which means there is no limit to the size. The format is the same as the ``max_size`` parameter
    :param bool required: Indicates whether the user must specify a file for the input. Default is ``False``.
    :param - label, name, help_text, other_html_attrs: Those arguments have the same meaning as for `input()`
    :return: When ``multiple=False``, a dict is returned::

        {
            'filename': file name，
            'content'：content of the file (in bytes),
            'mime_type': MIME type of the file,
            'last_modified': Last modified time (timestamp) of the file
        }

       If there is no file uploaded, return ``None``.

       When ``multiple=True``, a list is returned. The format of the list item is the same as the return value when ``multiple=False`` above.
       If the user does not upload a file, an empty list is returned.

    .. note::

        If uploading large files, please pay attention to the file upload size limit setting of the web framework.
        When using :func:`start_server() <pywebio.platform.tornado.start_server>` or
        :func:`path_deploy() <pywebio.platform.path_deploy>` to start the PyWebIO application,
        the maximum file size to be uploaded allowed by the web framework can be set through the ``max_payload_size`` parameter.

    .. exportable-codeblock::
        :name: file_upload_example
        :summary: `file_upload()` example

        # Upload a file and save to server                      # ..doc-only
        f = input.file_upload("Upload a file")                  # ..doc-only
        open('asset/'+f['filename'], 'wb').write(f['content'])  # ..doc-only

        imgs = file_upload("Select some pictures:", accept="image/*", multiple=True)
        for img in imgs:
            put_image(img['content'])

    """
    item_spec, valid_func, onchange_func = _parse_args(locals())
    item_spec['type'] = 'file'
    item_spec['max_size'] = parse_file_size(max_size) or platform_setting.MAX_PAYLOAD_SIZE
    item_spec['max_total_size'] = parse_file_size(max_total_size) or platform_setting.MAX_PAYLOAD_SIZE

    if platform_setting.MAX_PAYLOAD_SIZE:
        if item_spec['max_size'] > platform_setting.MAX_PAYLOAD_SIZE or \
                item_spec['max_total_size'] > platform_setting.MAX_PAYLOAD_SIZE:
            raise ValueError('The `max_size` and `max_total_size` value can not exceed the backend payload size limit. '
                             'Please increase the `max_total_size` of `start_server()`/`path_deploy()`')

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def slider(label: str = '', *, name: str = None, value: Union[int, float] = 0, min_value: Union[int, float] = 0,
           max_value: Union[int, float] = 100, step: int = 1, validate: Callable[[Any], Optional[str]] = None,
           onchange: Callable[[Any], None] = None, required: bool = None, help_text: str = None, **other_html_attrs):
    r"""Range input.

    :param int/float value: The initial value of the slider.
    :param int/float min_value: The minimum permitted value.
    :param int/float max_value: The maximum permitted value.
    :param int step: The stepping interval.
       Only available when ``value``, ``min_value`` and ``max_value`` are all integer.
    :param - label, name, validate, onchange, required, help_text, other_html_attrs: Those arguments have the same meaning as for `input()`
    :return int/float: If one of ``value``, ``min_value`` and ``max_value`` is float,
       the return value is a float, otherwise an int is returned.
    """
    item_spec, valid_func, onchange_func = _parse_args(locals())
    item_spec['type'] = 'slider'
    item_spec['float'] = any(isinstance(i, float) for i in (value, min_value, max_value))
    if item_spec['float']:
        item_spec['step'] = 'any'

    return single_input(item_spec, valid_func, lambda d: d, onchange_func)


def input_group(label: str = '', inputs: List = None, validate: Callable[[Dict], Optional[Tuple[str, str]]] = None,
                cancelable: bool = False):
    r"""Input group. Request a set of inputs from the user at once.

    :param str label: Label of input group.
    :param list inputs: Input items.
       The item of the list is the call to the single input function, and the ``name`` parameter need to be passed in the single input function.
    :param callable validate: validation function for the group. If provided, the validation function will be called when the user submits the form.

        Function signature: ``callback(data) -> (name, error_msg)``.
        ``validate`` receives the value of the entire group as a parameter. When the form value is valid, it returns ``None``.
        When an input item's value is invalid, it returns the ``name`` value of the item and an error message.
        For example:

    .. exportable-codeblock::
        :name: input_group-valid_func
        :summary: `input_group()` form validation

        def check_form(data):
            if len(data['name']) > 6:
                return ('name', 'Name to long!')
            if data['age'] <= 0:
                return ('age', 'Age cannot be negative!')

        data = input_group("Basic info",[
            input('Input your name', name='name'),
            input('Repeat your age', name='age', type=NUMBER)
        ], validate=check_form)

        put_text(data['name'], data['age'])

    :param bool cancelable: Whether the form can be cancelled. Default is ``False``.
        If ``cancelable=True``, a "Cancel" button will be displayed at the bottom of the form.

        Note: If the last input item in the group is `actions()`, ``cancelable`` will be ignored.

    :return: If the user cancels the form, return ``None``, otherwise a ``dict`` is returned,
        whose key is the ``name`` of the input item, and whose value is the value of the input item.
    """
    assert inputs is not None, 'Required `inputs` parameter in input_group()'

    spec_inputs = []
    preprocess_funcs = {}
    item_valid_funcs = {}
    onchange_funcs = {}
    for single_input_return in inputs:
        input_kwargs = single_input_kwargs(single_input_return)

        assert all(
            k in (input_kwargs or {})
            for k in ('item_spec', 'preprocess_func', 'valid_func', 'onchange_func')
        ), "`inputs` value error in `input_group`. Did you forget to add `name` parameter in input function?"

        input_name = input_kwargs['item_spec']['name']
        assert input_name, "`name` can not be empty!"
        if input_name in preprocess_funcs:
            raise ValueError('Duplicated input item name "%s" in same input group!' % input_name)
        preprocess_funcs[input_name] = input_kwargs['preprocess_func']
        item_valid_funcs[input_name] = input_kwargs['valid_func']
        onchange_funcs[input_name] = input_kwargs['onchange_func']
        spec_inputs.append(input_kwargs['item_spec'])

    if all('auto_focus' not in i for i in spec_inputs):  # No `auto_focus` parameter is set for each input item
        for i in spec_inputs:
            text_inputs = {TEXT, NUMBER, PASSWORD, SELECT, URL, FLOAT, DATE, TIME, DATETIME_LOCAL}
            if i.get('type') in text_inputs:
                i['auto_focus'] = True
                break

    spec = dict(label=label, inputs=spec_inputs, cancelable=cancelable)
    return input_control(spec, preprocess_funcs=preprocess_funcs,
                         item_valid_funcs=item_valid_funcs,
                         onchange_funcs=onchange_funcs,
                         form_valid_funcs=validate)


def parse_input_update_spec(spec):
    for key in spec:
        assert key not in {'action', 'buttons', 'code', 'inline', 'max_size', 'max_total_size', 'multiple', 'name',
                           'onchange', 'type', 'validate'}, '%r can not be updated' % key

    attributes = dict((k, v) for k, v in spec.items() if v is not None)
    if 'options' in spec:
        attributes['options'] = _parse_select_options(spec['options'])
    return attributes


def input_update(name: str = None, **spec):
    """Update attributes of input field.
    This function can only be called in ``onchange`` callback of input functions.

    :param str name: The ``name`` of the target input item.
       Optional, default is the name of input field which triggers ``onchange``
    :param spec: The input parameters need to be updated.
       Note that those parameters can not be updated:
       ``type``, ``name``, ``validate``, ``action``, ``code``, ``onchange``, ``multiple``

    An example of implementing dependent input items in an input group:

    .. exportable-codeblock::
        :name: input-update
        :summary: Dependent input items in input group

        country2city = {
            'China': ['Beijing', 'Shanghai', 'Hong Kong'],
            'USA': ['New York', 'Los Angeles', 'San Francisco'],
        }
        countries = list(country2city.keys())
        location = input_group("Select a location", [
            select('Country', options=countries, name='country',
                   onchange=lambda c: input_update('city', options=country2city[c])),
            select('City', options=country2city[countries[0]], name='city'),
        ])
        put_text(location)  # ..demo-only
    """
    task_id = get_current_task_id()
    k = 'onchange_trigger-' + task_id
    if k not in get_current_session().internal_save:
        raise RuntimeError("`input_update()` can only be called in `onchange` callback.")
    trigger_name = get_current_session().internal_save[k]

    if name is None:
        name = trigger_name

    attributes = parse_input_update_spec(spec)

    send_msg('update_input', dict(target_name=name, attributes=attributes))
