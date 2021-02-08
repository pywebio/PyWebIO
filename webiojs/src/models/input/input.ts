import {InputItem} from "./base";
import {Session} from "../../session";
import {deep_copy} from "../../utils"
import {state} from "../../state";


const common_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <div class="input-group">
        <input type="{{type}}" id="{{id_name}}" aria-describedby="{{id_name}}_action_btn"  {{#list}}list="{{list}}"{{/list}} class="form-control" >
        <datalist id="{{id_name}}-list">
            {{#datalist}} 
            <option>{{.}}</option> 
            {{/datalist}}
        </datalist>
        {{#action}} 
        <div class="input-group-append">
            <button class="btn btn-outline-secondary single-input-action-btn" type="button" id="{{id_name}}_action_btn" data-callbackid="{{callback_id}}">{{label}}</button>
        </div>
        {{/action}} 
        <div class="invalid-feedback">{{invalid_feedback}}</div>
        <div class="valid-feedback">{{valid_feedback}}</div>
    </div>
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;


export class Input extends InputItem {
    static accept_input_types: string[] = ["text", "password", "number", "color", "date", "range", "time", "email", "url"];

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element(): JQuery {
        let spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        if (spec.datalist)
            spec['list'] = id_name + '-list';

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

        let input_elem = this.element.find('#' + id_name);
        // blur事件时，发送当前值到服务器
        input_elem.on("blur", (e) => {
            if(this.get_value())
                this.send_value_listener(this, e)
        });

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

        this.update_input_helper(-1, attributes);
    }

    get_value(): any {
        return this.element.find('input').val();
    }
}

