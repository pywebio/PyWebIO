服务器-客户端通信协议
==========================

PyWebIO采用服务器-客户端架构，服务端运行任务代码，通过网络与客户端（也就是用户浏览器）交互

服务器与客户端有两种通信方式：WebSocket 和 Http 通信。

使用 Tornado或aiohttp 后端时，服务器与客户端通过 WebSocket 通信，使用 Flask或Django 后端时，服务器与客户端通过 Http 通信。

**WebSocket 通信：**

服务器与客户端通过WebSocket连接发送json序列化之后的PyWebIO消息

**Http 通信：**

* 客户端通过Http GET请求向后端轮训，后端返回json序列化之后的PyWebIO消息列表

* 当用户提交表单或者点击页面按钮后，客户端通过Http POST请求向后端提交数据

为方便区分，下文将由服务器向客户端发送的数据称作command，将客户端发向服务器的数据称作event

以下介绍command和event的格式

Command
------------

command由服务器->客户端，基本格式为::

    {
        "command": ""
        "task_id": ""
        "spec": {}
    }

各字段含义如下:

 * ``command`` 字段表示指令名

 * ``task_id`` 字段表示发送指令的Task id，客户端对于此命令的响应事件都会传递 task_id

 * ``spec`` 字段为指令的参数，不同指令参数不同

需要注意，以下不同命令的参数和 PyWebIO 的对应函数的参数大部分含义一致，但是也有些许不同。

以下分别对不同指令的 ``spec`` 字段进行说明：

input_group
^^^^^^^^^^^^^^^
显示一个输入表单

.. list-table:: ``spec`` 可用字段
   :header-rows: 1

   * - 字段
     - 是否必选
     - 类型
     - 字段说明

   * - label
     - False
     - str
     - 表单标题

   * - inputs
     - True
     - list
     - 输入项

   * - cancelable
     - False
     - bool
     - | 表单是否可以取消。
       | 若 ``cancelable=True`` 则会在表单底部显示一个"取消"按钮，
       | 用户点击取消按钮后，触发 ``from_cancel`` 事件


``inputs`` 字段为输入项组成的列表，每一输入项为一个 ``dict``，字段如下：

* label: 输入标签名。必选
* type: 输入类型。必选
* name: 输入项id。必选
* auto_focus: 自动获取输入焦点. 输入项列表中最多只能由一项的auto_focus为真
* help_text: 帮助文字
* 输入对应的html属性
* 不同输入类型的特有属性



输入类型目前有：

* text: 文本输入
* number: 数字输入
* password: 密码输入
* checkbox: 多选项
* radio: 单选项
* select: 下拉选择框(可单选/多选)
* textarea: 大段文本输入
* file: 文件上传
* actions: 如果表单最后一个输入元素为actions组件，则隐藏默认的"提交"/"重置"按钮

输入类型与html输入元素的对应关系:

* text: input[type=text]
* number: input[type=number]
* password: input[type=password]
* checkbox: input[type=checkbox]
* radio: input[type=radio]
* select: select  https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/select
* textarea: textarea  https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/textarea
* file: input[type=file]
* actions: button[type=submit] https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/button

不同输入类型的特有属性:

* text,number,password:
  * action: 在输入框一侧显示一个按钮。格式为 ``{label: 按钮标签, callback_id: 按钮回调id}``

* textarea:

  * code: Codemirror 参数, 见 :func:`pywebio.input.textarea` 的 ``code`` 参数

* select：

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``

* checkbox:

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
  * inline

* radio:

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
  * inline

* actions

  * buttons: 选项列表。``{label:选项标签, value:选项值, [type: 按钮类型 'submit'/'reset'/'cancel'/'callback'], [disabled:是否禁止选择]}`` .
    当 type 为 'callback' 时，value 字段表示回调函数的callback_id

* file:

   * multiple: 是否允许多文件上传
   * max_size: 单个文件的最大大小，超过限制将会禁止上传
   * max_total_size: 所有文件的最大大小，超过限制将会禁止上传

update_input
^^^^^^^^^^^^^^^

更新输入项，用于对当前显示表单中输入项的 ``spec`` 进行更新

命令 ``spec`` 可用字段：

* target_name: str 输入项的name值
* target_value: str，可选。 用于在checkbox, radio, actions输入中过滤input（这些类型的输入项包含多个html input元素）
* attributes: dist 需要更新的内容

  * valid_status: 为bool时，表示设置输入值的有效性，通过/不通过; 为0时，表示清空valid_status标志
  * value: 输入项的值
  * placeholder:
  * invalid_feedback
  * valid_feedback
  * action_result 仅在 actions 输入项中可用，表示设置输入项显示的文本
  * 输入项其他spec字段  // 不支持更新 on_focus on_blur inline label 字段


close_session
^^^^^^^^^^^^^^^
指示服务器端已经关闭连接。 ``spec`` 为空


destroy_form
^^^^^^^^^^^^^^^
销毁当前表单。 ``spec`` 为空

表单在页面上提交之后不会自动销毁，需要使用此命令显式销毁

output
^^^^^^^^^^^^^^^
输出内容

命令 ``spec`` 字段：

* type: 内容类型
* style: str 自定义样式
* scope: str 内容输出的域的css选择器。若CSS选择器匹配到页面上的多个容器，则内容会输出到每个匹配到的容器
* position: int 在输出域中输出的位置, 见 :ref:`输出函数的scope相关参数 <scope_param>`
* 不同type时的特有字段


``type`` 的可选值及特有字段：

* type: markdown, html

  * content: str 输出内容的原始字符串

* type: text

  * content: str 输出的文本
  * inline: True/False 文本是否末尾换行

* type: buttons

  * callback_id:
  * buttons:[ {value:, label:, [color:]},...]
  * small: bool，是否显示为小按钮样式
  * link: bool，是否显示为链接样式

* type: file

  * name: 下载保存为的文件名
  * content: 文件base64编码的内容

* type: table

  * data: 二维数组，表示表格数据，第一行为表头
  * span: 跨行/跨列的单元格信息，格式: {"[行id],[列id]": {"row":跨行数, "col":跨列数 }}

popup
^^^^^^^^^^^^^^^
显示弹窗

命令 spec 字段：

* title: 弹窗标题
* content: 数组，元素为字符串/对象，字符串表示html
* size: 弹窗窗口大小，可选值： ``large`` 、 ``normal`` 、 ``small``
* implicit_close: 是否可以通过点击弹窗外的内容或按下 `Esc` 键来关闭弹窗
* closable: 是否可由用户关闭弹窗. 默认情况下，用户可以通过点击弹窗右上角的关闭按钮来关闭弹窗，
  设置为 ``false`` 时弹窗仅能通过 ``popup_close`` command 关闭， ``implicit_close`` 参数被忽略.
* dom_id: 弹窗内容区的dom id

toast
^^^^^^^^^^^^^^^
显示通知消息

命令 spec 字段：

* content: 通知内容
* duration: 通知显示持续的时间，单位为毫秒
* position: 通知消息显示的位置，可以为 `'left'` / `'center'` / `'right'`
* color: 通知消息的背景颜色，格式为合法的css颜色值
* callback_id: 点击通知消息时的回调函数callback_id， 没有回调时为 null


close_popup
^^^^^^^^^^^^^^^
关闭正在显示的弹窗

该命令字段 ``spec`` 为 ``null``

set_env
^^^^^^^^^^^^^^^
环境配置

命令 spec 字段：

* title (str): 设定标题
* output_animation (bool): 是否在输出内容时，使用过渡动画
* auto_scroll_bottom (bool): 是否在内容输出时将页面自动滚动到底部
* http_pull_interval (int): HTTP轮训后端消息的周期（单位为毫秒，默认1000ms），仅在使用HTTP的连接中可用

output_ctl
^^^^^^^^^^^^^^^
输入控制

命令 spec 字段：

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
* scroll_to:
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