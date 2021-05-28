import {InputItem} from "./base";
import {deep_copy} from "../../utils"
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
    static accept_input_types: string[] = ["text", "password", "number", "float", "color", "date", "range", "time", "email", "url"];

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
        if (spec.onchange) {
            input_elem.on("input", (e) => {
                this.on_input_event("change", this);
            });
        }

        // 将额外的html参数加到input标签上
        const ignore_keys = {
            'action': '',
            'type': '',
            'label': '',
            'invalid_feedback': '',
            'valid_feedback': '',
            'help_text': '',
            'options': '',
            'datalist': '',
            'multiple': ''
        };
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }

        return this.element;
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
        let val= this.element.find('input').val();
        if(this.spec['type']=='number')
            val = parseInt(val as string);
        else if (this.spec['type']=='float')
            val = parseFloat(val as string);
        return val;
    }
}

