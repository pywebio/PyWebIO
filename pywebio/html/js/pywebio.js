(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        typeof define === 'function' && define.amd ? define(factory) :
            (global = global || self, global.WebIO = factory());
}(this, (function () {
    'use strict';

    const b64toBlob = (b64Data, contentType = 'application/octet-stream', sliceSize = 512) => {
        const byteCharacters = atob(b64Data);
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);

            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }

            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }

        const blob = new Blob(byteArrays, {type: contentType});
        return blob;
    };

    function extend(Child, Parent) {
        var F = function () {
        };
        F.prototype = Parent.prototype;
        Child.prototype = new F();
        Child.prototype.constructor = Child;
        Child.uber = Parent.prototype;
    }

    function make_set(arr) {
        var set = {};
        for (var idx in arr)
            set[arr[idx]] = '';
        return set;
    }

    function deep_copy(obj) {
        return JSON.parse(JSON.stringify(obj));
    }

    function LRUMap() {
        this.keys = [];
        this.map = {};

        this.push = function (key, value) {
            if (key in this.map)
                return console.error("LRUMap: key:%s already in map", key);
            this.keys.push(key);
            this.map[key] = value;
        };

        this.get_value = function (key) {
            return this.map[key];
        };
        this.get_top = function () {
            var top_key = this.keys[this.keys.length - 1];
            return this.map[top_key];
        };
        this.set_value = function (key, value) {
            if (!(key in this.map))
                return console.error("LRUMap: key:%s not in map when call `set_value`", key);
            this.map[key] = value;
        };

        this.move_to_top = function (key) {
            const index = this.keys.indexOf(key);
            if (index > -1) {
                this.keys.splice(index, 1);
                this.keys.push(key);
            } else {
                return console.error("LRUMap: key:%s not in map when call `move_to_top`", key);
            }
        };

        this.remove = function (key) {
            if (key in this.map) {
                delete this.map[key];
                this.keys.splice(this.keys.indexOf(key), 1);
            } else {
                return console.error("LRUMap: key:%s not in map when call `remove`", key);
            }
        };
    }


    // container 为带有滚动条的元素
    function body_scroll_to(target, position = 'top', complete, offset = 0) {
        var scrollTop = null;
        if (position === 'top')
            scrollTop = target.offset().top;
        else if (position === 'middle')
            scrollTop = target.offset().top + 0.5 * target[0].clientHeight - 0.5 * $(window).height();
        else if (position === 'bottom')
            scrollTop = target[0].clientHeight + target.offset().top - $(window).height();

        var container = $('body,html');
        var speed = Math.abs(container.scrollTop() - scrollTop - offset);
        if (scrollTop !== null)
            container.stop().animate({scrollTop: scrollTop + offset}, Math.min(speed, 500) + 100, complete);
    }

    // container 为带有滚动条的元素
    function box_scroll_to(target, container, position = 'top', complete, offset = 0) {
        var scrollTopOffset = null;
        if (position === 'top')
            scrollTopOffset = target[0].getBoundingClientRect().top - container[0].getBoundingClientRect().top;
        else if (position === 'middle')
            scrollTopOffset = target[0].getBoundingClientRect().top - container[0].getBoundingClientRect().top - container.height() * 0.5 + target.height() * 0.5;
        else if (position === 'bottom')
            scrollTopOffset = target[0].getBoundingClientRect().bottom - container[0].getBoundingClientRect().bottom;

        var speed = Math.min(Math.abs(scrollTopOffset + offset), 500) + 100;
        if (scrollTopOffset !== null)
            container.stop().animate({scrollTop: container.scrollTop() + scrollTopOffset + offset}, speed, complete);
    }

    var AutoScrollBottom = true;  // 是否有新内容时自动滚动到底部
    var OutputFixedHeight = false;  // 是否固定输出区域宽度

    OutputController.prototype.accept_command = ['output', 'output_ctl'];

    function OutputController(webio_session, container_elem) {
        this.webio_session = webio_session;
        this.container_elem = $(container_elem);
        this.md_parser = new Mditor.Parser();

        this.container_parent = this.container_elem.parent();
        this.body = $('html,body');
    }

    OutputController.prototype.scroll_bottom = function () {
        // 固定高度窗口滚动
        if (OutputFixedHeight)
            box_scroll_to(this.container_elem, this.container_parent, 'bottom', null, 30);
        // 整个页面自动滚动
        body_scroll_to(this.container_parent, 'bottom');
    };

    OutputController.prototype.handle_message = function (msg) {
        var scroll_bottom = false;
        if (msg.command === 'output') {
            const func_name = `get_${msg.spec.type}_element`;
            if (!(func_name in OutputController.prototype)) {
                return console.error('Unknown output type:%s', msg.spec.type);
            }

            var elem = OutputController.prototype[func_name].call(this, msg.spec);
            elem.hide();
            if (msg.spec.anchor !== undefined && this.container_elem.find(`#${msg.spec.anchor}`).length) {
                var pos = this.container_elem.find(`#${msg.spec.anchor}`);
                pos.empty().append(elem);
                elem.unwrap().attr('id', msg.spec.anchor);
            } else {
                if (msg.spec.anchor !== undefined)
                    elem.attr('id', msg.spec.anchor);

                if (msg.spec.before !== undefined) {
                    this.container_elem.find('#' + msg.spec.before).before(elem);
                } else if (msg.spec.after !== undefined) {
                    this.container_elem.find('#' + msg.spec.after).after(elem);
                } else {
                    this.container_elem.append(elem);
                    scroll_bottom = true;
                }
            }
            elem.fadeIn();
        } else if (msg.command === 'output_ctl') {
            this.handle_output_ctl(msg);
        }
        // 当设置了AutoScrollBottom、并且当前输出输出到页面末尾时，滚动到底部
        if (AutoScrollBottom && scroll_bottom)
            this.scroll_bottom();
    };

    // OutputController.prototype.get_[output_type]_element return a jQuery obj
    OutputController.prototype.get_text_element = function (spec) {
        var elem = spec.inline ? $('<span></span>') : $('<p></p>');
        spec.content = spec.content.replace(/ /g, '\u00A0');
        // make '\n' to <br/>
        var lines = (spec.content || '').split('\n');
        for (var idx = 0; idx < lines.length - 1; idx++)
            elem.append(document.createTextNode(lines[idx])).append('<br/>');
        elem.append(document.createTextNode(lines[lines.length - 1]));
        return elem;
    };

    OutputController.prototype.get_markdown_element = function (spec) {
        return $(this.md_parser.parse(spec.content));
    };

    OutputController.prototype.get_html_element = function (spec) {
        var nodes = $.parseHTML(spec.content, null, true);
        var elem = $(nodes);
        if (nodes.length > 1)
            elem = $('<div><div/>').append(elem);
        return elem;
    };

    OutputController.prototype.get_buttons_element = function (spec) {
        const btns_tpl = `<div class="form-group">{{#buttons}}
                             <button value="{{value}}" onclick="WebIO.DisplayAreaButtonOnClick(this, '{{callback_id}}')" class="btn btn-primary {{#small}}btn-sm{{/small}}">{{label}}</button> 
                          {{/buttons}}</div>`;
        var html = Mustache.render(btns_tpl, spec);
        return $(html);
    };

    OutputController.prototype.get_file_element = function (spec) {
        const html = `<div class="form-group"><button type="button" class="btn btn-link">${spec.name}</button></div>`;
        var element = $(html);
        var blob = b64toBlob(spec.content);
        element.on('click', 'button', function (e) {
            saveAs(blob, spec.name, {}, false);
        });

        return element;
    };

    OutputController.prototype.handle_output_ctl = function (msg) {
        if (msg.spec.title) {
            $('#title').text(msg.spec.title);  // 直接使用#title不规范 todo
            document.title = msg.spec.title;
        }
        if (msg.spec.output_fixed_height !== undefined) {
            OutputFixedHeight = msg.spec.output_fixed_height;
            if (msg.spec.output_fixed_height)
                $('.container').removeClass('no-fix-height');  // todo 不规范
            else
                $('.container').addClass('no-fix-height');  // todo 不规范
        }
        if (msg.spec.auto_scroll_bottom !== undefined)
            AutoScrollBottom = msg.spec.auto_scroll_bottom;
        if (msg.spec.set_anchor !== undefined) {
            this.container_elem.find(`#${msg.spec.set_anchor}`).attr('id', '');
            this.container_elem.append(`<div id="${msg.spec.set_anchor}"></div>`);
        }
        if (msg.spec.clear_before !== undefined)
            this.container_elem.find(`#${msg.spec.clear_before}`).prevAll().remove();
        if (msg.spec.clear_after !== undefined)
            this.container_elem.find(`#${msg.spec.clear_after}~*`).remove();
        if (msg.spec.scroll_to !== undefined) {
            var target = $(`#${msg.spec.scroll_to}`);
            if (!target.length) {
                console.error(`Anchor ${msg.spec.scroll_to} not found`);
            } else if (OutputFixedHeight) {
                box_scroll_to(target, this.container_parent, msg.spec.position);
            } else {
                body_scroll_to(target, msg.spec.position);
            }
        }
        if (msg.spec.clear_range !== undefined) {
            if (this.container_elem.find(`#${msg.spec.clear_range[0]}`).length &&
                this.container_elem.find(`#${msg.spec.clear_range[1]}`).length) {
                let removed = [];
                let valid = false;
                this.container_elem.find(`#${msg.spec.clear_range[0]}~*`).each(function () {
                    if (this.id === msg.spec.clear_range[1]) {
                        valid = true;
                        return false;
                    }
                    removed.push(this);
                    // $(this).remove();
                });
                if (valid)
                    $(removed).remove();
                else
                    console.warn(`clear_range not valid: can't find ${msg.spec.clear_range[1]} after ${msg.spec.clear_range[0]}`);
            }
        }
        if (msg.spec.remove !== undefined)
            this.container_elem.find(`#${msg.spec.remove}`).remove();
    };

    // 显示区按钮点击回调函数
    function DisplayAreaButtonOnClick(this_ele, callback_id) {
        if (WebIOSession_ === undefined)
            return console.error("can't invoke DisplayAreaButtonOnClick when WebIOController is not instantiated");

        var val = $(this_ele).val();
        WebIOSession_.send_message({
            event: "callback",
            task_id: callback_id,
            data: val
        });
    }

    const ShowDuration = 200; // ms, 显示表单的过渡动画时长

    FormsController.prototype.accept_command = ['input', 'input_group', 'update_input', 'destroy_form'];

    function FormsController(webio_session, container_elem) {
        this.webio_session = webio_session;
        this.container_elem = container_elem;

        this.form_ctrls = new LRUMap(); // task_id -> stack of FormGroupController

        var this_ = this;
        this._after_show_form = function () {
            if (!AutoScrollBottom)
                return;

            if (this_.container_elem.height() > $(window).height())
                body_scroll_to(this_.container_elem, 'top', () => {
                    $('[auto_focus="true"]').focus();
                });
            else
                body_scroll_to(this_.container_elem, 'bottom', () => {
                    $('[auto_focus="true"]').focus();
                });
        };

        // hide old_ctrls显示的表单，激活 task_id 对应的表单
        // 需要保证 task_id 对应有表单
        this._activate_form = function (task_id, old_ctrl) {
            var ctrls = this.form_ctrls.get_value(task_id);
            var ctrl = ctrls[ctrls.length - 1];
            if (ctrl === old_ctrl || old_ctrl === undefined) {
                return ctrl.element.show(ShowDuration, this_._after_show_form);
            }
            this.form_ctrls.move_to_top(task_id);
            var that = this;
            old_ctrl.element.hide(100, () => {
                // ctrl.element.show(100);
                // 需要在回调中重新获取当前前置表单元素，因为100ms内可能有变化
                var t = that.form_ctrls.get_top();
                if (t) t[t.length - 1].element.show(ShowDuration, this_._after_show_form);
            });
        };

        this.handle_message_ = function (msg) {
            // console.log('start handle_message %s %s', msg.command, msg.spec.label);
            this.consume_message(msg);
            // console.log('end handle_message %s %s', msg.command, msg.spec.label);
        };


        /*
        * 每次函数调用返回后，this.form_ctrls.get_top()的栈顶对应的表单为当前活跃表单
        * */
        this.handle_message = function (msg) {
            var old_ctrls = this.form_ctrls.get_top();
            var old_ctrl = old_ctrls && old_ctrls[old_ctrls.length - 1];
            var target_ctrls = this.form_ctrls.get_value(msg.task_id);
            if (target_ctrls === undefined) {
                this.form_ctrls.push(msg.task_id, []);
                target_ctrls = this.form_ctrls.get_value(msg.task_id);
            }

            // 创建表单
            if (msg.command in make_set(['input', 'input_group'])) {
                var ctrl = new FormController(this.webio_session, msg.task_id, msg.spec);
                target_ctrls.push(ctrl);
                this.container_elem.append(ctrl.element);
                this._activate_form(msg.task_id, old_ctrl);
            } else if (msg.command in make_set(['update_input'])) {
                // 更新表单
                if (target_ctrls.length === 0) {
                    return console.error('No form to current message. task_id:%s', msg.task_id);
                }
                target_ctrls[target_ctrls.length - 1].dispatch_ctrl_message(msg.spec);
                // 表单前置 removed
                // this._activate_form(msg.task_id, old_ctrl);
            } else if (msg.command === 'destroy_form') {
                if (target_ctrls.length === 0) {
                    return console.error('No form to current message. task_id:%s', msg.task_id);
                }
                var deleted = target_ctrls.pop();
                if (target_ctrls.length === 0)
                    this.form_ctrls.remove(msg.task_id);

                // 销毁的是当前显示的form
                if (old_ctrls === target_ctrls) {
                    var that = this;
                    deleted.element.hide(100, () => {
                        deleted.element.remove();
                        var t = that.form_ctrls.get_top();
                        if (t) t[t.length - 1].element.show(ShowDuration, this_._after_show_form);
                    });
                } else {
                    deleted.element.remove();
                }
            }
        }
    }


    function FormStack() {
        push();
        pop();
        empty();

        show();// 显示栈顶元素
        hide();// 隐藏栈顶元素
    }


    function FormController(webio_session, task_id, spec) {
        this.webio_session = webio_session;
        this.task_id = task_id;
        this.spec = spec;

        this.element = undefined;
        this.name2input_controllers = {};  // name -> input_controller

        this.create_element();
    }

    FormController.prototype.input_controllers = [FileInputController, CommonInputController, CheckboxRadioController, ButtonsController, TextareaInputController];

    FormController.prototype.create_element = function () {
        var tpl = `
        <div class="card" style="display: none">
            <h5 class="card-header">{{label}}</h5>
            <div class="card-body">
                <form>
                    <div class="input-container"></div>
                    <div class="ws-form-submit-btns">
                        <button type="submit" class="btn btn-primary">提交</button>
                        <button type="reset" class="btn btn-warning">重置</button>
                        {{#cancelable}}<button type="button" class="pywebio_cancel_btn btn btn-danger">取消</button>{{/cancelable}}
                    </div>
                </form>
            </div>
        </div>`;
        var that = this;

        const html = Mustache.render(tpl, {label: this.spec.label, cancelable: this.spec.cancelable});
        this.element = $(html);

        this.element.find('.pywebio_cancel_btn').on('click', function (e) {
            that.webio_session.send_message({
                event: "from_cancel",
                task_id: that.task_id,
                data: null
            });
        });

        // 如果表单最后一个输入元素为actions组件，则隐藏默认的"提交"/"重置"按钮
        if (this.spec.inputs.length && this.spec.inputs[this.spec.inputs.length - 1].type === 'actions')
            this.element.find('.ws-form-submit-btns').hide();

        // 输入控件创建
        var body = this.element.find('.input-container');
        for (var idx in this.spec.inputs) {
            var input_spec = this.spec.inputs[idx];
            var ctrl = undefined;
            for (var i in this.input_controllers) {
                var ctrl_cls = this.input_controllers[i];
                // console.log(ctrl_cls, ctrl_cls.prototype.accept_input_types);
                if (input_spec.type in make_set(ctrl_cls.prototype.accept_input_types)) {
                    ctrl = new ctrl_cls(this.webio_session, this.task_id, input_spec);
                    break;
                }
            }
            if (ctrl) {
                this.name2input_controllers[input_spec.name] = ctrl;
                body.append(ctrl.element);
            } else {
                console.error('Unvalid input type:%s', input_spec.type);
            }
        }

        // 事件绑定
        this.element.on('submit', 'form', function (e) {
            e.preventDefault(); // avoid to execute the actual submit of the form.
            var data = {};
            $.each(that.name2input_controllers, (name, ctrl) => {
                data[name] = ctrl.get_value();
            });
            that.webio_session.send_message({
                event: "from_submit",
                task_id: that.task_id,
                data: data
            });
        });
    };

    FormController.prototype.dispatch_ctrl_message = function (spec) {
        if (!(spec.target_name in this.name2input_controllers)) {
            return console.error('Can\'t find input[name=%s] element in curr form!', spec.target_name);
        }

        this.name2input_controllers[spec.target_name].update_input(spec);
    };


    function FormItemController(webio_session, task_id, spec) {
        this.webio_session = webio_session;
        this.task_id = task_id;
        this.spec = spec;
        this.element = undefined;

        var that = this;
        this.send_value_listener = function (e) {
            var this_elem = $(this);
            that.webio_session.send_message({
                event: "input_event",
                task_id: that.task_id,
                data: {
                    event_name: e.type.toLowerCase(),
                    name: that.spec.name,
                    value: that.get_value()
                }
            });
        };

        /*
        * input_idx: 更新作用对象input标签的索引, -1 为不指定对象
        * attributes：更新值字典
        * */
        this.update_input_helper = function (input_idx, attributes) {
            var attr2selector = {
                'invalid_feedback': 'div.invalid-feedback',
                'valid_feedback': 'div.valid-feedback',
                'help_text': 'small.text-muted'
            };
            for (var attribute in attr2selector) {
                if (attribute in attributes) {
                    if (input_idx === -1)
                        this.element.find(attr2selector[attribute]).text(attributes[attribute]);
                    else
                        this.element.find(attr2selector[attribute]).eq(input_idx).text(attributes[attribute]);
                    delete attributes[attribute];
                }
            }

            var input_elem = this.element.find('input,select,textarea');
            if (input_idx >= 0)
                input_elem = input_elem.eq(input_idx);

            if ('valid_status' in attributes) {
                var class_name = attributes.valid_status ? 'is-valid' : 'is-invalid';
                input_elem.removeClass('is-valid is-invalid').addClass(class_name);
                delete attributes.valid_status;
            }

            input_elem.attr(attributes);
        }
    }


    function CommonInputController(webio_session, task_id, spec) {
        FormItemController.apply(this, arguments);

        this.create_element();
    }

    CommonInputController.prototype.accept_input_types = ["text", "password", "number", "color", "date", "range", "time", "select", "file"];
    /*
    *
    * type=
    * */
    const common_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <input type="{{type}}" id="{{id_name}}" aria-describedby="{{id_name}}_help"  {{#list}}list="{{list}}"{{/list}} class="form-control" >
    <datalist id="{{id_name}}-list">
        {{#datalist}} 
        <option>{{.}}</option> 
        {{/datalist}}
    </datalist>
    <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
    <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;
    const select_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <select id="{{id_name}}" aria-describedby="{{id_name}}_help" class="form-control" {{#multiple}}multiple{{/multiple}}>
        {{#options}}
        <option value="{{value}}" {{#selected}}selected{{/selected}} {{#disabled}}disabled{{/disabled}}>{{label}}</option>
        {{/options}}
    </select>
    <div class="invalid-feedback">{{invalid_feedback}}</div>
    <div class="valid-feedback">{{valid_feedback}}</div>
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;
    CommonInputController.prototype.create_element = function () {
        var spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        if (spec.datalist)
            spec['list'] = id_name + '-list';

        var html;
        if (spec.type === 'select')
            html = Mustache.render(select_input_tpl, spec);
        else
            html = Mustache.render(common_input_tpl, spec);

        this.element = $(html);
        var input_elem = this.element.find('#' + id_name);

        // blur事件时，发送当前值到服务器
        input_elem.on('blur', this.send_value_listener);

        // 将额外的html参数加到input标签上
        const ignore_keys = {
            'type': '',
            'label': '',
            'invalid_feedback': '',
            'valid_feedback': '',
            'help_text': '',
            'options': '',
            'datalist': '',
            'multiple': ''
        };
        for (var key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }
    };

    CommonInputController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;

        this.update_input_helper(-1, attributes);
    };

    CommonInputController.prototype.get_value = function () {
        return this.element.find('input,select').val();
    };

    function TextareaInputController(webio_session, task_id, spec) {
        FormItemController.apply(this, arguments);

        this.create_element();
    }

    function load_codemirror_theme(theme, url_tpl = "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/theme/%N.min.css") {
        var cssId = 'codemirror_theme_' + theme;  // you could encode the css path itself to generate id..
        if (!document.getElementById(cssId)) {
            var head = document.getElementsByTagName('head')[0];
            var link = document.createElement('link');
            link.id = cssId;
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = url_tpl.replace('%N', theme);
            link.media = 'all';
            head.appendChild(link);
        }
    }

    TextareaInputController.prototype.accept_input_types = ["textarea"];
    const textarea_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <textarea id="{{id_name}}" aria-describedby="{{id_name}}_help" rows="{{rows}}" class="form-control" >{{value}}</textarea>
    <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
    <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;
    TextareaInputController.prototype.create_element = function () {
        var spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        var html = Mustache.render(textarea_input_tpl, spec);
        this.element = $(html);
        var input_elem = this.element.find('#' + id_name);

        // blur事件时，发送当前值到服务器
        // input_elem.on('blur', this.send_value_listener);

        // 将额外的html参数加到input标签上
        const ignore_keys = make_set(['value', 'type', 'label', 'invalid_feedback', 'valid_feedback', 'help_text', 'rows', 'code']);
        for (var key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }
        if (spec.code) {
            var that = this;
            var config = {
                'theme': 'base16-light',
                'mode': 'python',
                'lineNumbers': true,  // 显示行数
                'indentUnit': 4,  //缩进单位为4
                'styleActiveLine': true,  // 当前行背景高亮
                'matchBrackets': true,  //括号匹配
                'lineWrapping': true,  //自动换行
            };
            for (var k in that.spec.code)
                config[k] = that.spec.code[k];

            CodeMirror.autoLoadMode(that.code_mirror, config.mode);
            if (config.theme && config.theme !== 'base16-light')
                load_codemirror_theme(config.theme);

            setTimeout(function () {  // 需要等待当前表单被添加到文档树中后，再初始化CodeMirror，否则CodeMirror样式会发生错误
                that.code_mirror = CodeMirror.fromTextArea(that.element.find('textarea')[0], config);
                that.code_mirror.setSize(null, 20 * that.spec.rows);
            }, 100);

            setTimeout(function () {  // 需要等待当前表单显示后，重新计算表单高度
                // 重新计算表单高度
                that.element.parents('.card').height('auto');
            }, ShowDuration);
        }
    };

    TextareaInputController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;

        this.update_input_helper.call(this, -1, attributes);
    };

    TextareaInputController.prototype.get_value = function () {
        return this.element.find('textarea').val();
    };


    function CheckboxRadioController(webio_session, task_id, spec) {
        FormItemController.apply(this, arguments);

        this.create_element();
    }

    CheckboxRadioController.prototype.accept_input_types = ["checkbox", "radio"];

    const checkbox_radio_tpl = `
<div class="form-group">
    {{#label}}<label>{{label}}</label>{{/label}}
    {{#inline}}<br>{{/inline}}
    {{#options}}
    <div class="form-check {{#inline}}form-check-inline{{/inline}}">
        <input type="{{type}}" id="{{id_name_prefix}}-{{idx}}" name="{{name}}" value="{{value}}" {{#selected}}checked{{/selected}} {{#disabled}}disabled{{/disabled}} class="form-check-input">
        <label class="form-check-label" for="{{id_name_prefix}}-{{idx}}">
            {{label}}
        </label>
        <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
        <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    </div>
    {{/options}}
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;

    CheckboxRadioController.prototype.create_element = function () {
        var spec = deep_copy(this.spec);
        const id_name_prefix = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name_prefix'] = id_name_prefix;
        for (var idx in spec.options) {
            spec.options[idx]['idx'] = idx;
        }
        const html = Mustache.render(checkbox_radio_tpl, spec);
        var elem = $(html);
        this.element = elem;

        const ignore_keys = {'value': '', 'label': '', 'selected': ''};
        for (idx = 0; idx < this.spec.options.length; idx++) {
            var input_elem = elem.find('#' + id_name_prefix + '-' + idx);
            // blur事件时，发送当前值到服务器
            // checkbox_radio 不产生blur事件
            // input_elem.on('blur', this.send_value_listener);

            // 将额外的html参数加到input标签上
            for (var key in this.spec.options[idx]) {
                if (key in ignore_keys) continue;
                input_elem.attr(key, this.spec.options[idx][key]);
            }
        }
    };

    CheckboxRadioController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;
        var idx = -1;
        if ('target_value' in spec) {
            this.element.find('input').each(function (index) {
                if ($(this).val() === spec.target_value) {
                    idx = index;
                    return false;
                }
            });
        }
        this.update_input_helper(idx, attributes);
    };

    CheckboxRadioController.prototype.get_value = function () {
        if (this.spec.type === 'radio') {
            return this.element.find('input:checked').val() || '';
        } else {
            var value_arr = this.element.find('input').serializeArray();
            var res = [];
            var that = this;
            $.each(value_arr, function (idx, val) {
                if (val.name === that.spec.name)
                    res.push(val.value);
            });
            return res;
        }
    };

    function ButtonsController(webio_session, task_id, spec) {
        FormItemController.apply(this, arguments);

        this.submit_value = null;  // 提交表单时按钮组的value
        this.create_element();
    }

    ButtonsController.prototype.accept_input_types = ["actions"];

    const buttons_tpl = `
<div class="form-group">
    {{#label}}<label>{{label}}</label>  <br> {{/label}} 
    {{#buttons}}
    <button type="{{btn_type}}" data-type="{{type}}" value="{{value}}" aria-describedby="{{name}}_help" {{#disabled}}disabled{{/disabled}} class="btn btn-primary">{{label}}</button>
    {{/buttons}}
    <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
    <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    <small id="{{name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;

    ButtonsController.prototype.create_element = function () {
        for (var b of this.spec.buttons) b['btn_type'] = b.type === "submit" ? "submit" : "button";

        const html = Mustache.render(buttons_tpl, this.spec);
        this.element = $(html);

        var that = this;
        this.element.find('button').on('click', function (e) {
            var btn = $(this);
            if (btn.data('type') === 'submit') {
                that.submit_value = btn.val();
                // 不可以使用 btn.parents('form').submit()， 会导致input 的required属性失效
            } else if (btn.data('type') === 'reset') {
                btn.parents('form').trigger("reset");
            } else if (btn.data('type') === 'cancel') {
                that.webio_session.send_message({
                    event: "from_cancel",
                    task_id: that.task_id,
                    data: null
                });
            } else {
                console.error("`actions` input: unknown button type '%s'", btn.data('type'));
            }
        });
    };

    ButtonsController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;
        var idx = -1;
        if ('target_value' in spec) {
            this.element.find('button').each(function (index) {
                if ($(this).val() === spec.target_value) {
                    idx = index;
                    return false;
                }
            });
        }
        this.update_input_helper(idx, attributes);
    };

    ButtonsController.prototype.get_value = function () {
        return this.submit_value;
    };

    function FileInputController(webio_session, task_id, spec) {
        FormItemController.apply(this, arguments);
        this.data_url_value = null;
        this.create_element();
    }

    FileInputController.prototype.accept_input_types = ["file"];

    const file_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <div class="custom-file">
        <input type="file" name="{{name}}" class="custom-file-input" id="{{id_name}}" aria-describedby="{{id_name}}_help">
        <label class="custom-file-label" for="{{id_name}}">{{placeholder}}</label>
        <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
        <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
        <small id="{{id_name}}_help"  class="form-text text-muted">{{help_text}}</small>
    </div>
</div>`;

    FileInputController.prototype.create_element = function () {
        var spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;

        const html = Mustache.render(file_input_tpl, spec);
        this.element = $(html);
        var input_elem = this.element.find('input[type="file"]');

        const ignore_keys = {
            'label': '',
            'invalid_feedback': '',
            'valid_feedback': '',
            'help_text': '',
            'placeholder': ''
        };
        for (var key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }

        // 文件选中后先不通知后端
        var that = this;
        input_elem.on('change', function () {
            var file = input_elem[0].files[0];
            var fr = new FileReader();
            fr.onload = function () {
                that.data_url_value = {
                    'filename': file.name, 'dataurl': fr.result
                };
                console.log(that.data_url_value);
            };
            fr.readAsDataURL(file);
        });
        //  todo 通过回调的方式调用init
        setTimeout(bsCustomFileInput.init, ShowDuration + 100);
    };

    FileInputController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;
        this.update_input_helper(-1, attributes);
    };

    FileInputController.prototype.get_value = function () {
        return this.data_url_value;
    };


    /*
    * 会话
    * 向外暴露的事件：on_session_create、on_session_close、on_server_message
    * 提供的函数：start_session、send_message、close_session
    * */
    function WebIOSession() {
        this.on_session_create = () => {
        };
        this.on_session_close = () => {
        };
        this.on_server_message = (msg) => {
        };

        this.start_session = function (debug = false) {
        };
        this.send_message = function (msg) {
        };
        this.close_session = function () {
            this.on_session_close();
        };
    }

    function WebSocketWebIOSession(ws_url) {
        WebIOSession.apply(this);
        this.ws = null;
        this.debug = false;

        var url = new URL(ws_url);
        if (url.protocol !== 'wss:' && url.protocol !== 'ws:') {
            var protocol = url.protocol || window.location.protocol;
            url.protocol = protocol.replace('https', 'wss').replace('http', 'ws');
        }
        ws_url = url.href;

        var this_ = this;
        this.start_session = function (debug = false) {
            this.debug = debug;
            this.ws = new WebSocket(ws_url);
            this.ws.onopen = this.on_session_create;
            this.ws.onclose = this.on_session_close;
            this.ws.onmessage = function (evt) {
                var msg = JSON.parse(evt.data);
                if (debug) console.debug('>>>', msg);
                this_.on_server_message(msg);
            };
        };
        this.send_message = function (msg) {
            if (this.ws === null)
                return console.error('WebSocketWebIOSession.ws is null when invoke WebSocketWebIOSession.send_message. ' +
                    'Please call WebSocketWebIOSession.start_session first');
            this.ws.send(JSON.stringify(msg));
            if (this.debug) console.debug('<<<', msg);
        };
        this.close_session = function () {
            this.on_session_close();
            try {
                this.ws.close()
            } catch (e) {
            }
        };
    }


    function HttpWebIOSession(api_url, pull_interval_ms = 1000) {
        WebIOSession.apply(this);
        this.api_url = api_url;
        this.interval_pull_id = null;
        this.webio_session_id = '';
        this.debug = false;

        var this_ = this;
        this._on_request_success = function (data, textStatus, jqXHR) {
            var sid = jqXHR.getResponseHeader('webio-session-id');
            if (sid) this_.webio_session_id = sid;

            for (var idx in data) {
                var msg = data[idx];
                if (this_.debug) console.debug('>>>', msg);
                this_.on_server_message(msg);
            }
        };
        this.start_session = function (debug = false) {
            this.debug = debug;

            function pull() {
                $.ajax({
                    type: "GET",
                    url: this_.api_url,
                    contentType: "application/json; charset=utf-8",
                    dataType: "json",
                    headers: {"webio-session-id": this_.webio_session_id},
                    success: function (data, textStatus, jqXHR) {
                        this_._on_request_success(data, textStatus, jqXHR);
                        this_.on_session_create();
                    },
                    error: function () {
                        console.error('Http pulling failed');
                    }
                })
            }

            pull();
            this.interval_pull_id = setInterval(pull, pull_interval_ms);
        };
        this.send_message = function (msg) {
            if (this_.debug) console.debug('<<<', msg);
            $.ajax({
                type: "POST",
                url: this.api_url,
                data: JSON.stringify(msg),
                contentType: "application/json; charset=utf-8",
                dataType: "json",
                headers: {"webio-session-id": this_.webio_session_id},
                success: this_._on_request_success,
                error: function () {  // todo
                    console.error('Http push event failed, event data: %s', msg);
                }
            })
        };
        this.close_session = function () {
            this.on_session_close();
            clearInterval(this.interval_pull_id);
        };
    }

    var WebIOSession_;

    function WebIOController(webio_session, output_container_elem, input_container_elem) {
        WebIOSession_ = webio_session;
        webio_session.on_session_close = function () {
            $('#favicon32').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAByElEQVRYR82XLUzDUBDH/9emYoouYHAYMGCAYJAYEhxiW2EOSOYwkKBQKBIwuIUPN2g7gSPBIDF8GWbA4DAjG2qitEfesi6lbGxlXd5q393/fr333t07QpdfPp8f0nV9CcACEU0DGAOgN9yrAN6Y+QnATbVavcrlcp/dSFMnI9M0J1RV3WHmFQCJTvaN9RoRXbiuu28YxstfPm0BbNtOMPMeEW0C0LoMHDZzmPmIiHbT6XStlUZLgEKhMK5p2iWAyX8GDruVHMdZzmazr+GFXwCmac4oinINYCSm4L5M2fO8RcMwHoO6PwAaf37bh+BNCMdx5oOZaAKIPQdwF2Pa2yWwBGDOPxNNAMuyDohoK+a0t5Rj5sNMJrMtFusA4qopivLcw2mPyu14njclrmgdoFgsnjLzWlSVXuyJ6CyVSq2TqHDJZPI9QpHpJW7Qt1apVEbJsqwVIjqPSzWKDjOvCoBjItqI4hiXLTOfkG3b9wBm4xKNqPMgAMoAhiM6xmX+IQC+AKhxKUbUcQcCQPoWyD2E0q+h9EIkvRRLb0YD0Y4FhNQHiQCQ/iQTEFIfpX4Nl/os9yGkDiY+hNTRLNhSpQ2n4b7er/H8G7N6BRSbHvW5AAAAAElFTkSuQmCC');
            $('#favicon16').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA0ElEQVQ4T62TPQrCQBCF30tA8BZW9mJtY+MNEtKr2HkWK0Xtw+4NbGysxVorbyEKyZMNRiSgmJ/tZufNNzO7M0ThxHHc8zxvSnIIoPNyXyXt0zRdR1F0+gxhblhr25IWJMcA3vcFviRtSc6DILg5XyZ0wQB2AAbFir7YBwAjB8kAxpg1ycmfwZlM0iYMwyldz77vH3+U/Y2rJEn6NMYsSc7KZM+1kla01p4BdKsAAFwc4A6gVRHwaARQr4Xaj1j7G2sPUiOjnEMqL9PnDJRd5ycpJXsd2f2NIAAAAABJRU5ErkJggg==');
        };

        this.output_ctrl = new OutputController(webio_session, output_container_elem);
        this.input_ctrl = new FormsController(webio_session, input_container_elem);

        this.output_cmds = make_set(this.output_ctrl.accept_command);
        this.input_cmds = make_set(this.input_ctrl.accept_command);

        var this_ = this;
        webio_session.on_server_message = function (msg) {
            if (msg.command in this_.input_cmds)
                this_.input_ctrl.handle_message(msg);
            else if (msg.command in this_.output_cmds)
                this_.output_ctrl.handle_message(msg);
            else if (msg.command === 'close_session')
                webio_session.close_session();
            else
                console.error('Unknown command:%s', msg.command);
        };
    }

    return {
        'HttpWebIOSession': HttpWebIOSession,
        'WebSocketWebIOSession': WebSocketWebIOSession,
        'WebIOController': WebIOController,
        'DisplayAreaButtonOnClick': DisplayAreaButtonOnClick,
    }

})));