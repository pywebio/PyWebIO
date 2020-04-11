服务器-客户端通信协议
==========================

PyWebIO采用服务器-客户端架构，服务端运行任务代码，通过网络与客户端（也就是用户浏览器）交互
服务器与客户端有两种国内通信方式：WebSocket 和 Http 通信。
使用 Tornado 后端时，服务器与客户端通过 WebSocket 通信，使用 Flask 后端时，服务器与客户端通过 Http 通信。

WebSocket 通信：
服务器与客户端通过WebSocket连接发送json序列化之后的PyWebIO消息

Http 通信：
客户端通过Http GET请求向后端轮训，后端返回json序列化之后的PyWebIO消息列表
当用户提交表单后，客户端通过Http POST请求向后端提交输入的数据

在代码中，为进行区分，将服务器->客户端发送的数据称作command，将客户端->服务器的数据称作event

以下介绍command和event的格式

Command
------------

command由服务器->客户端，基本格式为::

    {
        "command": ""
        "task_id": ""
        "spec": {}
    }

其中 command 字段表示指令名
task_id 字段表示发送指令的Task id，客户端对于此命令的响应事件都会传递 task_id
spec 字段为指令的一些参数，不同指令参数不同

需要注意，以下不同命令的参数和对应的 PyWebIO 的响应函数大部分一致，但是也有些许不同。

以下分别对不同指令的参数进行说明：

input_group:
^^^^^^^^^^^^^^^
显示一个输入表单

.. list-table:: ``input`` spec 可用字段
   :widths: auto
   :header-rows: 1

   * - spec字段
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
     - 表单是否可以取消。若 ``cancelable=True`` 则会在表单底部显示一个"取消"按钮，用户点击取消按钮后，触发 ``from_cancel`` 事件


``inputs`` 字段为输入项组成的列表，每一输入项为一个 ``dict``，字段如下：

* label: 输入标签名。必选
* type: 输入类型。必选
* name: 输入项id。必选
* auto_focus
* help_text
* 输入对应的html属性
* 不同输入类型的特有属性



输入类型目前有：

* text
* number
* password
* checkbox
* radio
* select
* textarea
* file
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

输入类型的特有属性:
* textarea:

  * code：

* select：

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``

* checkbox:

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
  * inline

* radio:

  * options: 选项列表 ``{label:选项标签, value: 选项值, [selected:是否默认选中,] [disabled:是否禁止选中]}``
  * inline

* actions

  * buttons: 选项列表。``{label:选项标签, value:选项值, [type: 按钮类型 'submit'/'reset'/'cancel'], [disabled:是否禁止选择]}``



update_input:
^^^^^^^^^^^^^^^

更新输入项，用于对当前显示表单中输入项的spec进行更新

命令 spec 可用字段：

* target_name: input主键name
* target_value:str，可选。 用于在checkbox, radio, actions输入中过滤input（这些输入类型，包含多个html input元素）
* attributes: 更新内容 dist

  * valid_status: bool 输入值的有效性，通过/不通过
  * value:
  * placeholder:
  * invalid_feedback
  * valid_feedback
  * 输入项spec字段  // 不支持更新 on_focus on_blur inline label 字段


close_session:
^^^^^^^^^^^^^^^
用于服务器端关闭连接。无spec


destroy_form:
^^^^^^^^^^^^^^^
销毁当前表单。无spec
表单在页面上提交之后不会自动销毁，需要使用此命令显式销毁


output:
^^^^^^^^^^^^^^^
输入内容

命令 spec 字段：
* type
* before
* after
* anchor
* 不同type时的特有字段

不同type时的特有字段：


* type: markdown, html

  * content: ''

* type: text

  * inline: True/False
  * content: ''

* type: buttons

  * callback_id:
  * buttons:[ {value:, label:, },...]
  * small:

* type: file

  * name:
  * content:


output_ctl:
^^^^^^^^^^^^^^^
输入控制

命令 spec 字段：

* title: 设定标题
* output_fixed_height: 设置是否输出区固定高度
* auto_scroll_bottom: 设置有新内容时是否自动滚动到底部
* set_anchor
* clear_before
* clear_after
* clear_range:[,]
* scroll_to:
* position: top/middle/bottom 与scroll_to一起出现, 表示滚动页面，让锚点位于屏幕可视区域顶部/中部/底部
* remove: 将给定的锚点连同锚点处的内容移除

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

* event_name: 'blur'，表示输入项失去焦点
* name: 输入项name
* value: 输入项值

注意： checkbox_radio 不产生blur事件

callback
^^^^^^^^^^^^^^^
用户点击显示区的按钮时触发

在 ``callback`` 事件中，``task_id`` 为对应的 ``button`` 组件的 ``callback_id`` 字段；
事件的 ``data`` 为被点击button的 ``value``

from_submit:
^^^^^^^^^^^^^^^
用户提交表单时触发

事件 ``data`` 字段为表单 * ``name`` -> 表单值* 的字典

from_cancel:
^^^^^^^^^^^^^^^
取消输入表单

事件 ``data`` 字段为 ``None``

