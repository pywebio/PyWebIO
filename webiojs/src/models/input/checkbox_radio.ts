import {Session} from "../../session";
import {InputItem} from "./base";
import {deep_copy} from "../../utils"

const checkbox_radio_tpl = `
<div class="form-group">
    {{#label}}<label>{{label}}</label>{{/label}}
    {{#inline}}<br>{{/inline}}
    {{#options}}
    <div class="form-check {{#inline}}form-check-inline{{/inline}}">
        <input type="{{type}}" id="{{id_name_prefix}}-{{idx}}" name="{{name}}" {{#selected}}checked{{/selected}} {{#disabled}}disabled{{/disabled}} class="form-check-input">
        <label class="form-check-label" for="{{id_name_prefix}}-{{idx}}">
            {{label}}
        </label>
        <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
        <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    </div>
    {{/options}}
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;

export class CheckboxRadio extends InputItem {
    static accept_input_types: string[] = ["checkbox", "radio"];

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element(): JQuery {
        let spec = deep_copy(this.spec);
        const id_name_prefix = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name_prefix'] = id_name_prefix;
        for (let idx in spec.options) {
            spec.options[idx]['idx'] = idx;
        }
        const html = Mustache.render(checkbox_radio_tpl, spec);
        let elem = $(html);
        this.element = elem;

        let inputs = elem.find('input');
        for (let idx = 0; idx < spec.options.length; idx++)
            inputs.eq(idx).val(JSON.stringify(spec.options[idx].value));

        const ignore_keys = {'value': '', 'label': '', 'selected': ''};
        for (let idx = 0; idx < this.spec.options.length; idx++) {
            let input_elem = elem.find('#' + id_name_prefix + '-' + idx);
            // blur事件时，发送当前值到服务器
            // checkbox_radio 不产生blur事件
            // input_elem.on('blur', this.send_value_listener);

            // 将额外的html参数加到input标签上
            for (let key in this.spec.options[idx]) {
                if (key in ignore_keys) continue;
                input_elem.attr(key, this.spec.options[idx][key]);
            }
        }
        return this.element;
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        let idx = -1;
        if ('target_value' in spec) {
            this.element.find('input').each(function (index) {
                if (JSON.parse($(this).val() as string) === spec.target_value) {
                    idx = index;
                    return false;
                }
            });
        }
        this.update_input_helper(idx, attributes);
    }

    get_value(): any {
        if (this.spec.type === 'radio') {
            let raw_val = this.element.find('input:checked').val() || 'null';
            return JSON.parse(raw_val as string);
        } else {
            let value_arr = this.element.find('input').serializeArray();
            let res: any[] = [];
            let that = this;
            $.each(value_arr, function (idx, val) {
                if (val.name === that.spec.name)
                    res.push(JSON.parse(val.value as string));
                console.log(JSON.parse(val.value as string), typeof JSON.parse(val.value as string));
            });
            return res;
        }
    }
}



