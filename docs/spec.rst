Server-Client communication protocol
========================================

PyWebIO采用服务器-客户端架构，服务端运行任务代码，通过网络与客户端（也就是用户浏览器）交互

PyWebIO uses a server-client architecture, the server executes task code, and interacts with the client (that is, the user browser) through the network. This section is the protocol specification for the communication between PyWebIO server and client.

服务器与客户端有两种通信方式：WebSocket 和 Http 通信。

There are two communication methods between server and client: WebSocket and Http.

使用 Tornado或aiohttp 后端时，服务器与客户端通过 WebSocket 通信，使用 Flask或Django 后端时，服务器与客户端通过 Http 通信。

When using Tornado or aiohttp backend, the server and client communicate through WebSocket, when using Flask or Django backend, the server and client communicate through Http.

**WebSocket communication**

服务器与客户端通过WebSocket连接发送json序列化之后的PyWebIO消息
The server and the client send the PyWebIO message which are json serialized through WebSocket connection

**Http communication**

* 客户端通过Http GET请求向后端轮询，后端返回json序列化之后的PyWebIO消息列表

* The client polls the backend through Http GET requests, and the backend returns a list of PyWebIO messages serialized in json

* 当用户提交表单或者点击页面按钮后，客户端通过Http POST请求向后端提交数据

* When the user submits the form or clicks the page button, the client submits data to the backend through Http POST request

为方便区分，下文将由服务器向客户端发送的数据称作command，将客户端发向服务器的数据称作event

In the following, the data sent by the server to the client is called command, and the data sent by the client to the server is called event.

以下介绍command和event的格式

The following describes the format of command and event

Command
------------

command is sent by the server to the client. The basic format of command is::

    {
        "command": ""
        "task_id": ""
        "spec": {}
    }

Each fields are described as follows:

 * ``command`` : command name

 * ``task_id`` : Id of the task that send the command

 * ``spec`` : the data of the command, which is different depending on the command name

需要注意，以下不同命令的参数和 PyWebIO 的对应函数的参数大部分含义一致，但是也有些许不同。

The arguments shown above are merely the same with the parameters of corresponding PyWebIO functions.

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

update_input
^^^^^^^^^^^^^^^

Update the input item, you can update the ``spec`` of the input item of the currently displayed form

The ``spec`` fields of ``update_input`` commands:

* target_name: str The name of the target input item.
* target_value: str, optional. Used to filter options in checkbox, radio, actions type
* attributes: dist, fields need to be updated

  * valid_status: When it is bool, it means setting the state of the input value, pass/fail; when it is 0, it means clear the valid_status flag
  * value: Set the value of the item
  * placeholder
  * invalid_feedback
  * valid_feedback
  * other fields of item's ``spec`` // not support to inline adn label fields


close_session
^^^^^^^^^^^^^^^
Indicates that the server has closed the connection. ``spec`` of the command is empty.


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
* scope: str, CSS selector of the output container. If multiple containers are matched, the content will be output to every matched container
* position: int, see :ref:`scope - User manual <scope_param>`
* Other attributes of different types

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
  * link: bool, Whether to make button seem as link.

* type: file

  * name: File name when downloading
  * content: File content with base64 encoded

* type: table

  * data: Table data, which is a two-dimensional list, the first row is table header.
  * span: cell span info. Format: {"[row id],[col id]": {"row":row span, "col":col span }}

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

output_ctl
^^^^^^^^^^^^^^^
Output control

The ``spec`` fields of ``output_ctl`` commands:

* set_scope: 要创建的scope的名字

    * container: 新创建的scope的父scope的css选择器
    * position: 在父scope中创建此scope的位置. int, position>=0表示在父scope的第position个(从0计数)子元素的前面创建；position<0表示在父scope的倒数第position个(从-1计数)元素之后创建新scope
    * if_exist: scope已经存在时如何操作:

        - null/不指定时表示立即返回不进行任何操作
        - `'remove'` 表示先移除旧scope再创建新scope
        - `'clear'` 表示将旧scope的内容清除，不创建新scope

* clear: 需要清空的scope的css选择器
* clear_before
* clear_after
* clear_range:[,]
* scroll_to
* position: top/middle/bottom 与scroll_to一起出现, 表示滚动页面，让scope位于屏幕可视区域顶部/中部/底部
* remove: 将给定的scope连同scope处的内容移除

run_script
^^^^^^^^^^^^^^^
运行js代码

命令 spec 字段:

* code: 字符串格式的要运行的js代码
* args: 传递给代码的局部变量。字典类型，字典键表示变量名，字典值表示变量值(变量值需要可以被json序列化)

download
^^^^^^^^^^^^^^^
下载文件

命令 spec 字段：

* name: 下载保存为的文件名
* content: 文件base64编码的内容

Event
------------

客户端->服务器，事件格式::

    {
        event: ""
        task_id: ""
        data: object/str
    }

``event`` 表示事件名称。 ``data`` 为事件所携带的数据，其根据事件不同内容也会不同，不同事件对应的 ``data`` 字段如下:

input_event
^^^^^^^^^^^^^^^
表单发生更改时触发

* event_name: ``'blur'``，表示输入项失去焦点
* name: 输入项name
* value: 输入项值

注意： checkbox_radio 不产生blur事件

.. _callback_event:

callback
^^^^^^^^^^^^^^^
用户点击显示区的按钮时触发

在 ``callback`` 事件中，``task_id`` 为对应的 ``button`` 组件的 ``callback_id`` 字段；
事件的 ``data`` 为被点击button的 ``value``

from_submit
^^^^^^^^^^^^^^^
用户提交表单时触发

事件 ``data`` 字段为表单 ``name`` -> 表单值 的字典

from_cancel
^^^^^^^^^^^^^^^
取消输入表单

事件 ``data`` 字段为 ``None``

js_yield
^^^^^^^^^^^^^^^
js代码提交数据

事件 ``data`` 字段为相应的数据