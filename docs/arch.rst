Architecture
================

概念
------------

``Session`` 表示浏览器与程序交互产生的一次会话。PyWebIO在会话中运行 ``Task`` ，任务是

会话中除了起始的执行单元，也可以并发启动新的执行单元，在新的执行单元中也可以进行输入输出。

在用户端，相同会话中的不同的执行单元的输入是独立的，共享输出空间，但输出域的栈结构各自独立。

若用户正在填写一个执行单元的表单，会话中的其他执行单元也开始向用户请求输入，此时用户正在填写的表单将会隐藏，
新的输入表单将会显示给用户，当用户填写完新表单并提交后，旧表单重新显示，之前在旧表单上的输入也会保留。

在基于线程的会话中，会话中的每个执行单元都是一个线程

在基于协程的会话中，会话中的每个执行单元都是一个协程

除了并发执行的执行单元，会话中还有事件回调函数，目前就只有按钮控件可以绑定点击事件的回调函数。

架构
------------

会话内的每个执行单元使用唯一的task_id进行标识，由于会话内的输入需要区分执行单元，所以每个表单提交时，
除了表单的内容以外，还会携带表单所在的执行单元的task_id，这样，后台会话才可以知道该将表单数据传递给哪个执行单元。


.. image:: /assets/architecture.png

PyWebIO会话是由事件驱动的，这些事件来自用户在页面上的操作，比如提交表单，点击按钮，这些事件会通过http请求或websocket连接发送到后端框架。

后端框架维护有当前在线的Session实例，后端框架在收到用户提交的事件后，回调用相关Session实例的 ``send_client_event()`` 方法将事件发送至会话；

一个会话内会拥有至少一个执行单元，执行单元在调用PyWebIO的输入函数后会临时挂起，当会话收到用户的输入提交后，会话便将执行单元恢复执行，并提供用户输入的值。
执行单元内，任何输入输出的调用都会转换成一些命令序列发送给会话.

当后端框架通过HTTP与用户浏览器通信时，用户浏览器是以轮训的方式获取指令，会话会保存由执行单元生成的、还未发送到浏览器的命令序列，等待下次轮训时由后端框架取走。

当后端框架通过WebSocket与用户建立连接时，任何由执行单元发送到会话的命令都会立即发送到后端，并由后端通过WebSocket连接通知用户浏览器。

实现
------------

后端与Session的交互
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

后端框架负责从Session会话中获取来自PyWebIO的指令，并发送给用户浏览器；同时后端框架接收用户提交的数据，并发送给相应的会话实例。

Session暴露给后端框架的方法仅有 `Session.send_client_event <pywebio.session.base.Session.send_client_event>` 、 `Session.get_task_commands <pywebio.session.base.Session.get_task_commands>` 和 `Session.close <pywebio.session.base.Session.close>` 。


基于HTTP通信的后端的实现逻辑
"""""""""""""""""""""""""""""""""

**基于HTTP的前后端通信约定**

前端按照固定间隔使用GET请求轮训后端接口，在请求中使用 ``webio-session-id`` HTTP头来传递会话ID。

会话一开始时，会话ID由后端生成并通过响应中的 ``webio-session-id`` HTTP头返回给前端，后续前端的请求都会在请求头中使用 ``webio-session-id`` 字段传递会话ID。

前端产生的事件使用POST请求发送给后端。对于前端的每次轮训和事件提交请求，后端都会返回当前未执行的指令序列作为响应，前端收到响应后会依次执行指令。

**代码实现**

以Flask后端为例，Flask后端与Session的交互都在Flask视图函数中实现，视图函数通过调用 `pywebio.platform.flask.webio_view <./_modules/pywebio/platform/flask.html#webio_view>`_ 获取，
在 `webio_view` 中，先是实例化了一个 `pywebio.platform.httpbased.HttpHandler` ，然后声明了一个内部函数，这个内部函数就是Flask视图函数，
在视图函数内，先是实例化了一个 `pywebio.platform.flask.FlaskHttpContext` 对象，然后通过调用 ``HttpHandler.handle_request(FlaskHttpContext)`` 就获得了视图的响应。

这其中，FlaskHttpContext 的基类为 HttpContext ，HttpContext 接口各异的后端框架定义了一个统一的操作接口，用于从当前请求中获取请求相关的数据并设置请求的相应。 FlaskHttpContext 为HttpContext接口的Flask实现。

而 HttpHandle 负责维护Session实例并实现HTTP请求与Session之间的交互，HttpHandle 与后端框架相关的交互全都通过 HttpContext 操作。

HttpContext的生命周期为一次HTTP请求，HttpHandle的生命周期和整个后端框架的生命周期一致。

HttpHandler.handle_request 负责处理前端发送给后端的每一次请求，HttpHandler.handle_request 的处理流程如下：

1. 检测当前HTTP请求是否满足跨域设置
2. 根绝当前请求的 webio-session-id 头信息找到相应的Session实例，若不存在 webio-session-id 头则创建新会话并分配webio-session-id
3. 若当前请求为POST事件提交请求，则将提交的数据通过 Session.send_client_event 发送给Session
4. 通过调用 Session.get_task_commands 获取待执行的指令序列，并通过 HttpContext 向后端设置响应数据

此外，基于HTTP的会话，用户主动关闭会话时（比如关闭浏览器），后端无法立即感知，所以在HttpHandler.handle_request 中，
还会周期性地检测会话的最后活跃时间，将一段时间内不活跃的会话视为过期，所以在HttpHandler清理过期会话并调用 Session.close 释放会话内的资源。


基于WebSocket通信的后端的实现逻辑
""""""""""""""""""""""""""""""""""""
**基于WebSocket的前后端通信约定：**

浏览器与后端使用一个WebSocket连接来保持一个会话，后端的指令通过JSON序列化之后的消息实时发送给前端，前端用户触发的事件数据也通过JSON序列化之后发送给后端。

**代码实现**

以Tornado后端为例

webio_handler用于获取Tornado与前端进行通信的WebSocketHandler子类，其逻辑实现在 _webio_handler 中，由于WebSocket的有状态性，
WebSocketHandler子类的实现比基于HTTP通信的HttpHandler要简单许多，关键部分如下：

* 在WebSocket连接创建的时候初始化Session实例，并向Session对象注册了 on_task_command和on_session_close 回调，分别在新指令产生时和会话由执行单元关闭时由Session调用，
  用于实现WebSocketHandler向前端实时发送指令
* 在收到前端浏览器发送来的消息后，WebSocketHandler将收到的数据通过 Session.send_client_event 发送给Session
* 在WebSocket连接关闭时，调用 Session.close 释放会话内的资源。

session与执行单元(输入/输出)的交互
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

会话提供给执行单元的关键接口有:

* get_current_session : 静态方法，获取当前执行单元所属的会话实例
* get_current_task_id : 静态方法，获取当前执行单元所属的id
* send_task_command : 向会话发送指令
* next_client_event : 读取来自浏览器的属于当前执行单元的下一个事件
* register_callback : 向会话注册一个回调

同时，会话根据实现方式不同，还分别提供了 register_thread 和 run_async 用于启动新的执行单元。


**回调机制**

在会话中，为了能够响应用户在界面上的某些事件(比如点击了输出内容中的某个按钮)，于是设计了回调机制，可以在执行单元中使用register_callback向当前会话注册回调，然后执行单元会得到一个回调ID，
执行单元再通过相关指令让浏览器输出一些可以触发的控件，并向控件绑定回调ID，当用户触发控件后，前端将带有回调ID的 :ref:`回调事件 <callback_event>` 发回会话，会话会在专门的执行单元中或启动新执行单元中运行回调。

基于线程的会话实现
""""""""""""""""""""""""""""""""""""

在基于线程的会话中，每个执行单元都是一个线程，每个执行单元通过一条消息队列从会话接收来自用户的事件消息，当执行单元所需要的事件用户还没有提交时，执行单元便会挂起。

基于线程的会话使用线程ID作为执行单元的ID，在全局使用一个以线程id为key的字典来映射执行单元所属的会话实例，会话内不同执行单元的用户事件消息队列也通过执行单元ID进行索引。

使用 register_thread 启动新的执行单元时，也需要为新执行单元注册用户事件消息队列。

基于协程的会话实现
""""""""""""""""""""""""""""""""""""
在基于协程的会话中，每个执行单元都是一个由协程包装成的任务对象(Task)，当会话接收来自用户的事件消息后，便激活相应的任务对象，使得协程恢复运行。

由于基于协程的会话是单线程的，所以会话在激活任务对象前是通过将上下文信息保存在全局变量中来实现 get_current_session 和 get_current_task_id 方法，全局的上下文信息包含当前将要执行的会话的实例和执行单元的ID。


Script mode的实现
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Script mode 也是基于线程的，但由于全局仅存在一个会话，所有执行单元必定全部属于这个会话，所以也无需主动调用register_thread(thread)注册线程。

当PyWebIO检测到用户代码在后端Server还未启动的情况下就调用了PyWebIO交互函数时，便会启动Script mode：

1. 在新线程中启动后端Server
2. 启动浏览器打开后端Server运行的地址
3. 在第一次与用户建立连接时初始化会话

script mode的会话类继承了基于线程的会话类，并修改了部分方法:

* 构造函数 : 仅允许script mode会话类被初始化一次
* get_current_session : 直接返回全局的会话对象
* get_current_task_id : 除了返回当前线程id，还会自动将当前线程使用 register_thread 注册到会话中

相关对象的文档
------------------------

.. autoclass:: pywebio.platform.httpbased.HttpHandler
   :members:

.. autoclass:: pywebio.platform.flask.FlaskHttpContext
   :members:

.. autoclass:: pywebio.session.base.Session
   :members:


