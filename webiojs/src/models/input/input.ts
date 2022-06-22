import {InputItem} from "./base";
import {deep_copy, make_set} from "../../utils"
import {state} from "../../state";

const datalist_tpl = `
{{#datalist}} 
<option>{{.}}</option> 
{{/datalist}}`;

const common_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    {{#action}}<div class="input-group">{{/action}} 
        <input type="{{type}}" id="{{id_name}}" aria-describedby="{{id_name}}_action_btn" list="{{id_name}}-list" class="form-control" >
        <datalist id="{{id_name}}-list">
            ${datalist_tpl}
        </datalist>
        {{#action}} 
        <div class="input-group-append">
            <button class="btn btn-outline-secondary single-input-action-btn" type="button" id="{{id_name}}_action_btn" data-callbackid="{{callback_id}}">{{label}}</button>
        </div>
        {{/action}} 
        <div class="invalid-feedback">{{invalid_feedback}}</div>
        <div class="valid-feedback">{{valid_feedback}}</div>
    {{#action}}</div>{{/action}} 
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;


export class Input extends InputItem {
    static accept_input_types: string[] = ["text", "password", "number", "float", "color", "date", "range", "time", "email", "url", "datetime-local"];
    previous_value = '';

    constructor(spec: any, task_id: string, on_input_event: (event_name: string, input_item: InputItem) => void) {
        super(spec, task_id, on_input_event);
    }

    create_element(): JQuery {
        let spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        if (spec['type'] == 'float') spec['type'] = 'text';

        let html = Mustache.render(common_input_tpl, spec);

        this.element = $(html);

        this.element.find(`#${id_name}_action_btn`).on('click', function (e) {
            let btn = $(this);
            state.CurrentSession.send_message({
                event: "callback",
                task_id: btn.data('callbackid') as string,
                data: null
            });
        });

        let input_elem = this.element.find('input');
        if (spec.onblur) {
            // blur事件时，发送当前值到服务器
            input_elem.on("blur", (e) => {
                if (this.get_value())
                    this.on_input_event("blur", this);
            });
        }

        input_elem.on("input", (e) => {
            this.rectify_input()
            if (spec.onchange) {
                this.on_input_event("change", this);
            }
        });

        // 将额外的html参数加到input标签上
        const ignore_keys = make_set(['action', 'type', 'label', 'invalid_feedback', 'valid_feedback', 'help_text',
            'options', 'datalist', 'multiple', 'onchange', 'onblur']);
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }

        return this.element;
    }

    rectify_input() {
        let val = '' + this.element.find('input').val() as string;
        let re;
        if (this.spec['type'] == 'number') {
            re = /^[+-]?\d*$/;
        } else if (this.spec['type'] == 'float') {
            re = /^[+-]?\d*\.?\d*$/;
        }
        if (re && !re.test(val)) {
            this.element.find('input').val(this.previous_value);
        } else {
            this.previous_value = val;
        }
    }

    // 检查输入项的有效性，在表单提交时调用
    check_valid(): boolean {
        let valid = !Number.isNaN(this.get_value()) || this.element.find('input').val() === '';
        if (!valid) {
            this.update_input_helper(-1, {
                'valid_status': false
            });
        } else {
            this.update_input_helper(-1, {
                'valid_status': 0, // remove the valid status
            });
        }
        return valid;
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        if ('datalist' in attributes) {
            const datalist_html = Mustache.render(datalist_tpl, {datalist: attributes.datalist});
            this.element.find('datalist').empty().append(datalist_html);
            delete attributes['datalist'];
        }

        this.update_input_helper(-1, attributes);
    }

    get_value(): any {
        this.rectify_input()
        let val = this.element.find('input').val();
        if (this.spec['type'] == 'number')
            val = parseInt(val as string);
        else if (this.spec['type'] == 'float')
            val = parseFloat(val as string);
        return val;
    }
}

