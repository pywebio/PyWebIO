2/7
应该不需要msg_id，ws连接是有状态的，不需要msg_id来标示状态。当在多个状态之间切换时，前后端周知，可以同步切换状态。

每个ws连接维护一个coro栈，栈顶为当前活跃coro，来消息后激活该coro；前端维护输入栈，栈顶为当前活跃表单，表单控制消息作用于栈顶表单。
触发上区的一些事件回调时，产生新的coro，压栈；前端当前表单未提交成功又来新表单时，当前表单压栈，显示新表单
每个ws连接维护一个回调列表。当在上区输出带有回调的UI元素时，保存回调；当上区清屏时，同时清空回调列表，回调列表相保存锚点信息，clear_before(pos) clear_after

设计哲学：下区，阻塞等待回应区，同步交互，栈式结构；上区，瀑布流UI区，通过回调函数交互。

2/8
需要 msg_id,  或者说是 coro_id/thread_id
每个ws连接维护一个coros字典，每次根据消息的coro_id判断进入哪一个coro；前端维护form字典: coro_id -> form_handler栈，根据指令coro_id判断作用于哪一个表单，并将其置顶。
触发上区的一些事件回调时，产生新的coro；前端当前表单未提交成功又来新表单时，当前表单隐藏，显示新表单




2/9
NOTE: 
含有yield的函数一定是生成器，不管会不会执行到 （比如在分支里）

coro.send 内部可能还会存在 激活协程的调用，要禁止嵌套创建协程Task或者将Global改成栈式存储


2/10
当前问题：
    对于tornado coro的支持不是很友好:连续 yield tornado coro时，无法在yield间隙调度到其他coro执行 [todo]
    使用tornado Future的callback应该可以解决
    
对于yield input()和 yield input_group([input(), input()])语法的实现：
    input()返回一个msg对象，task接收到后，处理 发送
    比上述更好地实现 [ok]
    
    
2/11
用户输入函数中，对结果无影响的非法参数可以以warnning而不是异常的方式提示用户 [ok]



2/12 
发现tornado对于一个ws连接，若on——message不结束，无法进行下一个