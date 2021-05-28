import {InputItem} from "./base";
import {deep_copy, make_set} from "../../utils";

const slider_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <input type="range" class="form-control-range" name="{{name}}" min="{{min_value}}" max="{{max_value}}" value="{{value}}" id="{{id_name}}">
    <div class="invalid-feedback">{{invalid_feedback}}</div>
    <div class="valid-feedback">{{valid_feedback}}</div>
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;

export class Slider extends InputItem {
    static accept_input_types: string[] = ["slider"];

    files: Blob[] = []; // Files to be uploaded
    valid = true;

    constructor(spec: any, task_id: string, on_input_event: (event_name: string, input_item: InputItem) => void) {
        super(spec, task_id, on_input_event);
    }

    create_element(): JQuery {
        let spec = deep_copy(this.spec);
        spec['id_name'] = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));

        const html = Mustache.render(slider_input_tpl, spec);
        this.element = $(html);
        let input_elem = this.element.find('input[type="range"]');

        const ignore_keys = make_set(['value', 'type', 'label', 'invalid_feedback', 'valid_feedback',
            'help_text', 'min_value', 'max_value', 'id_name', 'name', 'float']);
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }

        if (spec.onblur) {
            // blur事件时，发送当前值到服务器
            input_elem.on("blur", (e) => {
                this.on_input_event("blur", this);
            });
        }
        if (spec.onchange) {
            input_elem.on("change", (e) => {
                this.on_input_event("change", this);
            });
        }

        return this.element;
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        this.update_input_helper(-1, attributes);
    }

    get_value(): any {
        let val = this.element.find('input[type="range"]').val();
        if (this.spec['float'])
            val = parseFloat(val as string);
        else
            val = parseInt(val as string);
        return val;
    }

}



