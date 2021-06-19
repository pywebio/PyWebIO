import {Command, Session} from "../session";
import {error_alert, LRUMap, make_set, serialize_json} from "../utils";
import {InputItem} from "../models/input/base"
import {state} from '../state'
import {all_input_items} from "../models/input"
import {CommandHandler} from "./base"
import {close_input, show_input} from "../ui";
import {t} from "../i18n";

/*
* 整个输入区域的控制类
* 管理当前活跃和非活跃的表单
* */
export class InputHandler implements CommandHandler {
    accept_command: string[] = ['input', 'input_group', 'update_input', 'destroy_form'];

    session: Session;
    private form_ctrls: LRUMap; // task_id -> stack of FormGroupController
    private readonly container_elem: JQuery;

    constructor(session: Session, container_elem: JQuery) {
        this.session = session;
        this.container_elem = container_elem;
        this.form_ctrls = new LRUMap(); // task_id -> stack of FormGroupController
    }

    private _after_show_form() {
        // 解决表单显示后动态添加内容，表单宽高不变的问题
        setTimeout(() => {
            let curr_card = $('#input-cards > .card')[0];
            curr_card.style.height = "unset";
            curr_card.style.width = "unset";
        }, 50);

        show_input();

        let old_ctrls = this.form_ctrls.get_top();
        if (old_ctrls)
            old_ctrls[old_ctrls.length - 1].after_show();

        if (state.AutoFocusOnInput)
            $('[auto_focus="true"]').focus();
    };

    // hide old_ctrls显示的表单，激活 task_id 对应的表单
    // 需要保证 task_id 对应有表单
    private _activate_form(task_id: string, old_ctrl: InputItem) {
        let ctrls = this.form_ctrls.get_value(task_id);
        let ctrl = ctrls[ctrls.length - 1];
        if (ctrl === old_ctrl || old_ctrl === undefined) {
            return ctrl.element.show(state.ShowDuration, () => {
                this._after_show_form()
            });
        }
        this.form_ctrls.move_to_top(task_id);
        old_ctrl.element.hide(100, () => {
            // ctrl.element.show(100);
            // 需要在回调中重新获取当前前置表单元素，因为100ms内可能有变化
            let t = this.form_ctrls.get_top();
            if (t) t[t.length - 1].element.show(state.ShowDuration, () => {
                this._after_show_form()
            });
        });
    };


    /*
    * 每次函数调用返回后，this.form_ctrls.get_top()的栈顶对应的表单为当前活跃表单
    * */
    handle_message(msg: Command) {
        let old_ctrls = this.form_ctrls.get_top();
        let old_ctrl = old_ctrls && old_ctrls[old_ctrls.length - 1];
        let target_ctrls = this.form_ctrls.get_value(msg.task_id);
        if (target_ctrls === undefined) {
            this.form_ctrls.push(msg.task_id, []);
            target_ctrls = this.form_ctrls.get_value(msg.task_id);
        }

        // 创建表单
        if (msg.command in make_set(['input', 'input_group'])) {
            let ctrl = new FormController(this.session, msg.task_id, msg.spec);
            target_ctrls.push(ctrl);
            this.container_elem.append(ctrl.create_element());
            ctrl.after_add_to_dom();
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
            let deleted = target_ctrls.pop() as FormController;
            if (target_ctrls.length === 0)
                this.form_ctrls.remove(msg.task_id);

            // 销毁的是当前显示的form
            if (old_ctrls === target_ctrls) {
                deleted.element.hide(100, () => {
                    deleted.element.remove();
                    close_input();

                    let t = this.form_ctrls.get_top();
                    if (t) t[t.length - 1].element.show(state.ShowDuration, () => {
                        this._after_show_form()
                    });
                });
            } else {
                deleted.element.remove();
                close_input();
            }
        }
    }
}


/*
* 表单控制器
* */
class FormController {
    static input_items: { [input_type: string]: typeof InputItem } = {};

    session: Session;

    element: JQuery = null;

    private task_id: string;
    private spec: any;
    // name -> input_controller
    private name2input: { [i: string]: InputItem } = {};
    private show_count: number = 0;

    public static register_inputitem(cls: typeof InputItem) {
        for (let type of cls.accept_input_types) {
            if (type in this.input_items)
                throw new Error(`duplicated accept_input_types:[${type}] in ${cls} and ${this.input_items[type]}`);
            this.input_items[type] = cls;
        }
    }

    constructor(session: Session, task_id: string, spec: any) {
        this.session = session;
        this.task_id = task_id;
        this.spec = spec;

        // this.create_element();
    }


    create_element(): JQuery {
        let tpl = `
            <div class="card" style="display: none">
                <h5 class="card-header">{{label}}</h5>
                <div class="card-body">
                    <form>
                        <div class="input-container"></div>
                        <div class="ws-form-submit-btns">
                            <button type="submit" class="btn btn-primary">${t("submit")}</button>
                            <button type="reset" class="btn btn-warning">${t("reset")}</button>
                            {{#cancelable}}<button type="button" class="pywebio_cancel_btn btn btn-danger">${t("cancel")}</button>{{/cancelable}}
                        </div>
                    </form>
                </div>
            </div>`;
        let that = this;

        const html = Mustache.render(tpl, {label: this.spec.label, cancelable: this.spec.cancelable});
        let element = $(html);

        element.find('.pywebio_cancel_btn').on('click', function (e) {
            element.find('button').prop("disabled", true);
            that.session.send_message({
                event: "from_cancel",
                task_id: that.task_id,
                data: null
            });
        });

        // 隐藏默认的"提交"/"重置"按钮
        if (this.spec.inputs.length && this.spec.inputs[this.spec.inputs.length - 1].type === 'actions') {
            for (let btn of this.spec.inputs[this.spec.inputs.length - 1].buttons) {
                if (btn.type === 'submit') {
                    element.find('.ws-form-submit-btns').hide();
                    break;
                }
            }
        }

        // 输入控件创建
        let body = element.find('.input-container');
        for (let idx in this.spec.inputs) {
            let input_spec = this.spec.inputs[idx];
            if (!(input_spec.type in FormController.input_items))
                throw new Error(`Unknown input type '${input_spec.type}'`);
            let item_class = FormController.input_items[input_spec.type];
            let item = new item_class(input_spec, this.task_id, (event, input_item) => {
                this.session.send_message({
                    event: "input_event",
                    task_id: this.task_id,
                    data: {
                        event_name: event,
                        name: input_spec.name,
                        value: input_item.get_value()
                    }
                });
            });
            this.name2input[input_spec.name] = item;

            body.append(item.create_element());
        }

        // submit event
        element.on('submit', 'form', function (e) {
            e.preventDefault(); // avoid to execute the actual submit of the form.

            element.find('button').prop("disabled", true);

            for (let name in that.name2input)
                if (!that.name2input[name].check_valid())
                    return error_alert(t("error_in_input"));

            let data_keys: string[] = [];
            let data_values: any[] = [];
            $.each(that.name2input, (name, ctrl) => {
                data_keys.push(name as string);
                data_values.push(ctrl.get_value());
            });

            let on_process = (loaded: number, total: number) => {
            };
            // show process bar when there is a file input field
            for (let item of that.spec.inputs) {
                if (item.type == 'file') {
                    on_process = that.make_progress();
                    break;
                }
            }
            Promise.all(data_values).then((values) => {
                let input_data: { [i: string]: any } = {};
                let files: Blob[] = [];
                for (let idx in data_keys) {
                    input_data[data_keys[idx]] = values[idx];
                    if (that.spec.inputs[idx].type == 'file') {
                        input_data[data_keys[idx]] = [];
                        files.push(...values[idx]);
                    }
                }
                let msg = {
                    event: "from_submit",
                    task_id: that.task_id,
                    data: input_data
                };
                if (files.length) {
                    that.session.send_buffer(new Blob([serialize_json(msg), ...files], {type: 'application/octet-stream'}), on_process);
                } else {
                    that.session.send_message(msg, on_process);
                }
            });

        });

        this.element = element;
        return element;
    };

    // 显示提交进度条，返回进度更新函数
    make_progress() {
        let html = `<div class="progress" style="margin-top: 4px;">
                        <div class="progress-bar bg-info progress-bar-striped progress-bar-animated" role="progressbar"
                             style="width: 0%;" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%
                        </div>
                    </div>`;
        let elem = $(html);
        this.element.find('.card-body').append(elem);

        let bar = elem.find('.progress-bar');
        return function (loaded: number, total: number) {
            let progress = "" + (100.0 * loaded / total).toFixed(1);
            bar[0].style.width = progress + "%";
            bar.attr("aria-valuenow", progress);
            bar.text(progress + "%");
        }
    };

    dispatch_ctrl_message(spec: any) {
        // 恢复原本可点击的按钮
        this.element.find('button:not([data-pywebio-disabled])').prop("disabled", false);
        // 移除上传进度条
        this.element.find('.progress').remove();

        if (!(spec.target_name in this.name2input)) {
            return console.error('Can\'t find input[name=%s] element in curr form!', spec.target_name);
        }

        this.name2input[spec.target_name].update_input(spec);
    };

    // 在表单加入DOM树后，触发输入项的on_add_to_dom回调
    after_add_to_dom() {
        for (let name in this.name2input) {
            this.name2input[name].after_add_to_dom();
        }
    }

    // 在表单被显示后，触发输入项的after_show回调
    after_show() {
        for (let name in this.name2input) {
            this.name2input[name].after_show(this.show_count === 0);
        }
        this.show_count += 1;
    }
}

for (let item of all_input_items)
    FormController.register_inputitem(item);