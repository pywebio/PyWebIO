服务器->客户端
{
    command: ""
    coro_id: ""
   	spec: {}
}
命令名:
    参数1:
    参数2:
    


## 命令

继承关系：
全局：
    <button>
    输入类：
        <input>
        <select>
        <textarea>

全局参数 (带*号的必须, ～可选, ^为非html属性)
    *^label
    ^help_text
    ^invalid_feedback
    ^valid_feedback
    输入类全局参数


<input> 类命令  // 全局 <input> 参数  ref: https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/input
    *name
    *type
    readonly/disabled：bool 禁用的控件的值在提交表单时也不会被提交
    required:
    value:
    placeholder： placeholder 属性是提示用户内容的输入格式。某些情况下 placeholder 属性对用户不可见, 所以当没有它时也需要保证form能被理解。
    ^on_focus
    ^on_blur
    ^inline  // type==checkbox,radio
    ^options // type==checkbox,radio , 字典列表 {*value:, *label:, checked，disabled }



<button>
ref https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/button

<select>
ref https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/select

<textarea>
ref https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/textarea


input_group:
    label:
    inputs: [ <input>, ] // 若只有一个input 则可以忽略其label属性



控制类指令
update_input:
    target_name: input主键name
    ～target_value:str 用于checkbox, radio 过滤input 
    attributes: {
        valid_status: bool 输入值的有效性，通过/不通过
        value:
        placeholder:
        ...  // 不支持 on_focus on_blur inline label
    }
    

destroy_form:
    无spec

output:
    type: text
    content: {}


客户端->服务器
{
    event: ""
    coro_id: ""
   	data: {}
}
事件名:
    数据项1:
    数据项2:

input_event
    event_name: on_blur
    name:
    value:

from_submit:
    


