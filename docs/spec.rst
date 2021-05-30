Server-Client communication protocol
========================================

PyWebIO uses a server-client architecture, the server executes task code, and interacts with the client (that is, the user browser) through the network. This section introduce the protocol specification for the communication between PyWebIO server and client.

There are two communication methods between server and client: WebSocket and Http.

When using Tornado or aiohttp backend, the server and client communicate through WebSocket, when using Flask or Django backend, the server and client communicate through Http.

**WebSocket communication**

The server and the client send json-serialized message through WebSocket connection

**Http communication**

* The client polls the backend through Http GET requests, and the backend returns a list of PyWebIO messages serialized in json

* When the user submits the form or clicks the button, the client submits data to the backend through Http POST request

In the following, the data sent by the server to the client is called command, and the data sent by the client to the server is called event.

The following describes the format of command and event

Command
------------

Command is sent by the server to the client. The basic format of command is::

    {
        "command": ""
        "task_id": ""
        "spec": {}
    }

Each fields are described as follows:

 * ``command`` : command name

 * ``task_id`` : Id of the task that send the command

 * ``spec`` : the data of the command, which is different depending on the command name

Note that: the arguments shown above are merely the same with the parameters of corresponding PyWebIO functions,
but there are some differences.

The following describes the ``spec`` fields of different commands:

input_group
^^^^^^^^^^^^^^^
Show a form in user's browser.

.. list-table:: fields of ``spec``
   :header-rows: 1

   * - Field
     - Required
     - Type
     - Description

   * - label
     - False
     - str
     - Title of the form

   * - inputs
     - True
     - list
     - Input items

   * - cancelable
     - False
     - bool
     - | Whether the form can be cancelled。
       | If cancelable=True, a “Cancel” button will be displayed at the bottom of the form.
       | A ``from_cancel`` event is triggered after the user clicks the cancel button.

The ``inputs`` field is a list of input items, each input item is a ``dict``, the fields of the item are as follows:

* label: Label of input field, required.
* type: Input type, required.
* name: Identifier of the input field, required.
* onchange: bool, whether to push input value when input change
* onbulr: bool, whether to push input value when input field `onblur`
* auto_focus: Set focus automatically. At most one item of ``auto_focus`` can be true in the input item list
* help_text: Help text for the input
* Additional HTML attribute of the input element
* Other attributes of different input types

Currently supported ``type`` are:

* text: Plain text input
* number: Number input
* password: Password input
* checkbox: Checkbox
* radio: Radio
* select: Drop-down selection
* textarea: Multi-line text input
* file: File uploading
* actions: Actions selection.

Correspondence between different input types and html input elements:

* text: input[type=text]
* number: input[type=number]
* float: input[type=text], and transform input value to float
* password: input[type=password]
* checkbox: input[type=checkbox]
* radio: input[type=radio]
* select: select  https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/select
* textarea: textarea  https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/textarea
* file: input[type=file]
* actions: button[type=submit] https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/button

Unique attributes of different input types:

* text,number,password:
  * action: Display a button on the right of the input field.
    The format of ``action`` is ``{label: button label, callback_id: button click callback id}``

* textarea:

  * code: Codemirror options, same as ``code`` parameter of :func:`pywebio.input.textarea`

* select：

  * options: ``{label:, value: , [selected:,] [disabled:]}``

* checkbox:

  * options: ``{label:, value: , [selected:,] [disabled:]}``
  * inline

* radio:

  * options: ``{label:, value: , [selected:,] [disabled:]}``
  * inline

* actions

  * buttons: ``{label:, value:, [type: 'submit'/'reset'/'cancel'], [disabled:]}`` .


* file:

   * multiple: Whether to allow upload multiple files.
   * max_size: The maximum size of a single file, in bytes.
   * max_total_size: The maximum size of all files, in bytes.

* slider

   * min_value: The minimum permitted value.
   * max_value: The maximum permitted value.
   * step: The stepping interval.
   * float: If need return a float value

update_input
^^^^^^^^^^^^^^^

Update the input item, you can update the ``spec`` of the input item of the currently displayed form

The ``spec`` fields of ``update_input`` commands:

* target_name: str The name of the target input item.
* target_value: str, optional. Used to filter item in checkbox, radio
* attributes: dist, fields need to be updated

  * valid_status: When it is bool, it means setting the state of the input value, pass/fail; when it is 0, it means clear the valid_status flag
  * value: Set the value of the item
  * label
  * placeholder
  * invalid_feedback
  * valid_feedback
  * help_text
  * options: only available in checkbox, radio and select type
  * other fields of item's ``spec`` // not support the ``inline`` field


close_session
^^^^^^^^^^^^^^^
Indicates that the server has closed the connection. ``spec`` of the command is empty.

set_session_id
^^^^^^^^^^^^^^^
Send current session id to client, used to reconnect to server (Only available in websocket connection).
``spec`` of the command is session id.

destroy_form
^^^^^^^^^^^^^^^
Destroy the current form. ``spec`` of the command is empty.

Note: The form will not be automatically destroyed after it is submitted, it needs to be explicitly destroyed using this command

output
^^^^^^^^^^^^^^^
Output content

The ``spec`` fields of ``output`` commands:

* type: content type
* style: str, Additional css style
* container_selector: The css selector of output widget's container. If empty(default), use widget self as container
* container_dom_id: The dom id set to output widget's container.
* scope: str, CSS selector of the output container. If multiple containers are matched, the content will be output to every matched container
* position: int, see :ref:`scope - User manual <scope_param>`
* Other attributes of different types

``container_selector`` and ``container_dom_id`` is used to implement output context manager.

Unique attributes of different types:

* type: markdown

  * content: str
  * options: dict, `marked.js <https://github.com/markedjs/marked>`_ options
  * sanitize: bool, Whether to enable a XSS sanitizer for HTML

* type: html

  * content: str
  * sanitize: bool, Whether to enable a XSS sanitizer for HTML

* type: text

  * content: str
  * inline: bool, Use text as an inline element (no line break at the end of the text)

* type: buttons

  * callback_id:
  * buttons:[ {value:, label:, [color:]},...]
  * small: bool, Whether to enable small button
  * group: bool, Whether to group the buttons together
  * link: bool, Whether to make button seem as link.
  * outline: bool, Whether enable outline style.

* type: file

  * name: File name when downloading
  * content: File content with base64 encoded

* type: table

  * data: Table data, which is a two-dimensional list, the first row is table header.
  * span: cell span info. Format: {"[row id],[col id]": {"row":row span, "col":col span }}

* type: pin

  * input: input spec, same as the item of ``input_group.inputs``

pin_value
^^^^^^^^^^^^^^^

The ``spec`` fields of ``pin_value`` commands:

* name

pin_update
^^^^^^^^^^^^^^^

The ``spec`` fields of ``pin_update`` commands:

* name
* attributes: dist, fields need to be updated

pin_wait
^^^^^^^^^^^^^^^

The ``spec`` fields of ``pin_wait`` commands:

* names


popup
^^^^^^^^^^^^^^^
Show popup

The ``spec`` fields of ``popup`` commands:

* title
* content
* size: ``large``, ``normal``, ``small``
* implicit_close
* closable
* dom_id: DOM id of popup container element

toast
^^^^^^^^^^^^^^^
Show a notification message

The ``spec`` fields of ``popup`` commands:

* content
* duration
* position: `'left'` / `'center'` / `'right'`
* color: hexadecimal color value starting with '#'
* callback_id


close_popup
^^^^^^^^^^^^^^^
Close the current popup window.

``spec`` of the command is empty.

set_env
^^^^^^^^^^^^^^^
Config the environment of current session.

The ``spec`` fields of ``set_env`` commands:

* title (str)
* output_animation (bool)
* auto_scroll_bottom (bool)
* http_pull_interval (int)
* input_panel_fixed (bool)
* input_panel_min_height (int)
* input_panel_init_height (int)
* input_auto_focus (bool)

output_ctl
^^^^^^^^^^^^^^^
Output control

The ``spec`` fields of ``output_ctl`` commands:

* set_scope: scope name

    * container: Specify css selector to the parent scope of target scope.
    * position: int, The index where this scope is created in the parent scope.
    * if_exist: What to do when the specified scope already exists:

        - null: Do nothing
        - `'remove'`: Remove the old scope first and then create a new one
        - `'clear'`: Just clear the contents of the old scope, but don’t create a new scope

* clear: css selector of the scope need to clear
* clear_before
* clear_after
* clear_range:[,]
* scroll_to
    * position: top/middle/bottom, Where to place the scope in the visible area of the page
* remove: Remove the specified scope

run_script
^^^^^^^^^^^^^^^
run javascript code in user's browser

The ``spec`` fields of ``run_script`` commands:

* code: str, code
* args: dict, Local variables passed to js code
* eval: bool, whether to submit the return value of javascript code

download
^^^^^^^^^^^^^^^
Send file to user

The ``spec`` fields of ``download`` commands:

* name: str, File name when downloading
* content: str, File content in base64 encoding.

Event
------------

Event is sent by the client to the server. The basic format of event is::

    {
        event: event name
        task_id: ""
        data: object/str
    }

The ``data`` field is the data carried by the event, and its content varies according to the event.
The ``data`` field of different events is as follows:

input_event
^^^^^^^^^^^^^^^
Triggered when the form changes

* event_name: Current available value is ``'blur'``, which indicates that the input item loses focus
* name: name of input item
* value: value of input item

note: checkbox and radio do not generate blur events

.. _callback_event:

callback
^^^^^^^^^^^^^^^
Triggered when the user clicks the button in the page

In the ``callback`` event, ``task_id`` is the ``callback_id`` field of the ``button``;
The ``data`` of the event is the ``value`` of the button that was clicked

from_submit
^^^^^^^^^^^^^^^
Triggered when the user submits the form

The ``data`` of the event is a dict, whose key is the name of the input item, and whose value is the value of the input item.

from_cancel
^^^^^^^^^^^^^^^
Cancel input form

The ``data`` of the event is ``None``

js_yield
^^^^^^^^^^^^^^^
submit data from js

The ``data`` of the event is the data need to submit