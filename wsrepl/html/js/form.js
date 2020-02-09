(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
        typeof define === 'function' && define.amd ? define(factory) :
            (global = global || self, global.WSREPL = factory());
}(this, (function () {
    'use strict';

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

    function OutputController(ws_client, container_elem) {
        this.ws_client = ws_client;
        this.container_elem = container_elem;
        this.md_parser = new Mditor.Parser();

        this.handle_message = function (msg) {
            this.container_elem[0].innerHTML += this.md_parser.parse(msg.spec.content);
        }
    }

    OutputController.prototype.accept_command = ['output'];


    FormsController.prototype.accept_command = ['input', 'input_group', 'update_input', 'destroy_form'];

    function FormsController(ws_client, container_elem) {
        this.ws_client = ws_client;
        this.container_elem = container_elem;

        this.form_ctrls = new LRUMap(); // coro_id -> stack of FormGroupController

        // hide old_ctrls显示的表单，激活coro_id对应的表单
        // 需要保证 coro_id 对应有表单
        this._activate_form = function (coro_id, old_ctrl) {
            var ctrls = this.form_ctrls.get_value(coro_id);
            var ctrl = ctrls[ctrls.length - 1];
            if (ctrl === old_ctrl || old_ctrl === undefined)
                return ctrl.element.show(100);
            this.form_ctrls.move_to_top(coro_id);
            old_ctrl.element.hide(100, () => {
                ctrl.element.show(100);
            });
        };

        /*
        * 每次函数调用返回后，this.form_ctrls.get_top()的栈顶对应的表单为当前活跃表单
        * */
        this.handle_message = function (msg) {
            var old_ctrls = this.form_ctrls.get_top();
            var old_ctrl = old_ctrls && old_ctrls[old_ctrls.length - 1];
            var target_ctrls = this.form_ctrls.get_value(msg.coro_id);
            if (target_ctrls === undefined) {
                this.form_ctrls.push(msg.coro_id, []);
                target_ctrls = this.form_ctrls.get_value(msg.coro_id);
            }

            // 创建表单
            if (msg.command in make_set(['input', 'input_group'])) {
                var ctrl = new FormController(this.ws_client, msg.coro_id, msg.spec);
                target_ctrls.push(ctrl);
                this.container_elem.append(ctrl.element);
                this._activate_form(msg.coro_id, old_ctrl);
            } else if (msg.command in make_set(['update_input'])) {
                // 更新表单
                if (target_ctrls.length === 0) {
                    return console.error('No form to current message. coro_id:%s', msg.coro_id);
                }
                target_ctrls[target_ctrls.length - 1].dispatch_ctrl_message(msg.spec);
                // 表单前置
                this._activate_form(msg.coro_id, old_ctrl);
            } else if (msg.command === 'destroy_form') {
                if (target_ctrls.length === 0) {
                    return console.error('No form to current message. coro_id:%s', msg.coro_id);
                }
                var deleted = target_ctrls.pop();
                if (target_ctrls.length === 0)
                    this.form_ctrls.remove(msg.coro_id);

                // 销毁的是当前显示的form
                if (old_ctrls === target_ctrls) {
                    var that = this;
                    deleted.element.hide(100, () => {
                        var t = that.form_ctrls.get_top();
                        if (t) t[t.length - 1].element.show(100);
                    });
                }
            }
            // todo: 如果当前栈顶key is not coro_id, hide show, move to top
        }
    }


    function FormStack() {
        push();
        pop();
        empty();

        show();// 显示栈顶元素
        hide();// 隐藏栈顶元素
    }


    function FormController(ws_client, coro_id, spec) {
        this.ws_client = ws_client;
        this.coro_id = coro_id;
        this.spec = spec;

        this.element = undefined;
        this.input_controllers = {};  // name -> input_controller

        this.create_element();
    }

    FormController.prototype.create_element = function () {
        var tpl = `
        <div class="card" style="display: none">
            <h5 class="card-header">{{label}}</h5>
            <div class="card-body">
                <form>
                    <div class="input-container"></div>
                    <button type="submit" class="btn btn-primary">提交</button>
                    <button type="reset" class="btn btn-warning">重置</button>
                </form>
            </div>
        </div>`;

        const html = Mustache.render(tpl, {label: this.spec.label});
        this.element = $(html);

        // 输入控件创建
        var body = this.element.find('.input-container');
        for (var idx in this.spec.inputs) {
            var i = this.spec.inputs[idx];
            var ctrl;
            if (i.type in make_set(CommonInputController.prototype.accept_input_types)) {
                ctrl = new CommonInputController(this.ws_client, this.coro_id, i);
            } else if (i.type in make_set(CheckboxRadioController.prototype.accept_input_types)) {
                ctrl = new CheckboxRadioController(this.ws_client, this.coro_id, i);
            }

            this.input_controllers[i.name] = ctrl;
            body.append(ctrl.element);
        }

        // 事件绑定
        var that = this;
        this.element.on('submit', 'form', function (e) {
            e.preventDefault(); // avoid to execute the actual submit of the form.
            var inputs = $(this).serializeArray();
            var data = {};
            $.each(inputs, (idx, item) => {
                if (data[item.name] === undefined) data[item.name] = [];
                data[item.name].push(item.value);
            });
            ws.send(JSON.stringify({
                event: "from_submit",
                coro_id: that.coro_id,
                data: data
            }));
        })
    };

    FormController.prototype.dispatch_ctrl_message = function (spec) {
        if (!(spec.target_name in this.input_controllers)) {
            return console.error('Can\'t find input[name=%s] element in curr form!' , spec.target_name);
        }

        this.input_controllers[spec.target_name].update_input(spec);
    };


    function FormItemController(ws_client, coro_id, spec) {
        this.ws_client = ws_client;
        this.coro_id = coro_id;
        this.spec = spec;
        this.element = undefined;

        var that = this;
        this.send_value_listener = function (e) {
            var this_elem = $(this);
            that.ws_client.send(JSON.stringify({
                event: "input_event",
                coro_id: that.coro_id,
                data: {
                    event_name: e.type.toLowerCase(),
                    name: this_elem.attr('name'),
                    value: this_elem.val()
                }
            }));
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

            var input_elem = this.element.find('input');
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


    function CommonInputController(ws_client, coro_id, spec) {
        FormItemController.apply(this, arguments);

        this.create_element();
    }

    CommonInputController.prototype.accept_input_types = ["text", "password", "number", "color", "date", "range", "time"];
    /*
    *
    * type=
    * */
    const common_input_tpl = `
<div class="form-group">
    <label for="{{id_name}}">{{label}}</label>
    <input type="{{type}}" id="{{id_name}}" aria-describedby="{{id_name}}_help"  class="form-control">
    <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
    <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;
    CommonInputController.prototype.create_element = function () {
        var spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        const html = Mustache.render(common_input_tpl, spec);

        this.element = $(html);
        var input_elem = this.element.find('#' + id_name);

        // blur事件时，发送当前值到服务器
        input_elem.on('blur', this.send_value_listener);

        // 将额外的html参数加到input标签上
        const ignore_keys = {'type': '', 'label': '', 'invalid_feedback': '', 'valid_feedback': '', 'help_text': ''};
        for (var key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }
    };

    CommonInputController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;

        this.update_input_helper(-1, attributes);
    };

    function CheckboxRadioController(ws_client, coro_id, spec) {
        FormItemController.apply(this, arguments);

        this.create_element();
    }

    CheckboxRadioController.prototype.accept_input_types = ["checkbox", "radio"];

    const checkbox_radio_tpl = `
<div class="form-group">
    <label>{{label}}</label> {{#inline}}<br>{{/inline}}
    {{#options}}
    <div class="form-check {{#inline}}form-check-inline{{/inline}}">
        <input type="{{type}}" id="{{id_name_prefix}}-{{idx}}" class="form-check-input" name="{{name}}" value="{{value}}">
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

        const ignore_keys = {'value': '', 'label': ''};
        for (idx = 0; idx < this.spec.options.length; idx++) {
            var input_elem = elem.find('#' + id_name_prefix + '-' + idx);
            // blur事件时，发送当前值到服务器
            input_elem.on('blur', this.send_value_listener);

            // 将额外的html参数加到input标签上
            for (var key in this.spec.options[idx]) {
                if (key in ignore_keys) continue;
                input_elem.attr(key, this.spec[key]);
            }
        }
    };

    CheckboxRadioController.prototype.update_input = function (spec) {
        var attributes = spec.attributes;
        var idx = -1;
        if ('target_value' in spec) {
            this.element.find('input').each(function (index) {
                if ($(this).val() == spec.target_value) {
                    idx = index;
                    return false;
                }
            });
        }
        this.update_input_helper(idx, attributes);
    };


    function WSREPLController(ws_client, output_container_elem, input_container_elem) {
        this.output_ctrl = new OutputController(ws_client, output_container_elem);
        this.input_ctrl = new FormsController(ws_client, input_container_elem);

        this.output_cmds = make_set(this.output_ctrl.accept_command);
        this.input_cmds = make_set(this.input_ctrl.accept_command);
        this.handle_message = function (msg) {
            if (msg.command in this.input_cmds)
                this.input_ctrl.handle_message(msg);
            else if (msg.command in this.output_cmds)
                this.output_ctrl.handle_message(msg);
            else
                console.error('Unknown command:%s', msg.command);
        };
    }

    return {
        'WSREPLController': WSREPLController
    }

})));