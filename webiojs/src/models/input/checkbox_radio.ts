import {Session} from "../../session";
import {InputItem} from "./base";
import {deep_copy} from "../../utils"

const options_tpl = `
{{#options}}
<div class="form-check {{#inline}}form-check-inline{{/inline}}">
    <input type="{{type}}" id="{{id_name_prefix}}-{{idx}}" name="{{name}}" {{#selected}}checked{{/selected}} {{#disabled}}disabled{{/disabled}} class="form-check-input">
    <label class="form-check-label" for="{{id_name_prefix}}-{{idx}}">
        {{label}}
    </label>
</div>
{{/options}}
`;

const checkbox_radio_tpl = `
<div class="form-group">
    {{#label}}<label>{{label}}</label>{{/label}}
    {{#inline}}<br>{{/inline}}
    ${options_tpl}
    <div class="invalid-feedback">{{invalid_feedback}}</div> 
    <div class="valid-feedback">{{valid_feedback}}</div>
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;

export class CheckboxRadio extends InputItem {
    static accept_input_types: string[] = ["checkbox", "radio"];

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element(): JQuery {
        let spec = this.setup_spec();
        const html = Mustache.render(checkbox_radio_tpl, spec);
        let elem = $(html);
        this.setup_input_options(elem, spec.options);
        this.element = elem;
        return this.element;
    }

    setup_spec() {
        let spec = deep_copy(this.spec);
        const id_name_prefix = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name_prefix'] = id_name_prefix;
        for (let idx in spec.options) {
            spec.options[idx]['idx'] = idx;
        }
        return spec;
    }

    setup_input_options(elem: JQuery, options: any) {
        let inputs = elem.find('input');
        for (let idx = 0; idx < options.length; idx++) {
            let input_elem = inputs.eq(idx);
            input_elem.on("blur", (e) => {
                this.send_value_listener(this, e);
            });
            if(this.spec.onchange){
                input_elem.on("change", (e) => {
                    this.send_value_listener(this, e);
                });
            }
            input_elem.val(JSON.stringify(options[idx].value));
            // 将额外的html参数加到input标签上
            for (let key in options[idx]) {
                if (key in {'value': '', 'label': '', 'selected': ''}) continue;
                input_elem.attr(key, options[idx][key]);
            }
        }
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

        if ('options' in attributes) {
            this.spec.options = attributes.options;
            let spec = this.setup_spec();
            const html = Mustache.render(options_tpl, spec);
            this.element.find('.form-check').remove();
            this.element.find('.invalid-feedback').before(html);
            this.setup_input_options(this.element, spec.options);
            delete attributes['options'];
        }

        if ('valid_status' in attributes) {
            this.element.find('.invalid-feedback,.valid-feedback').hide();
            if (attributes.valid_status === true)
                this.element.find('.valid-feedback').show();
            else if (attributes.valid_status === false)
                this.element.find('.invalid-feedback').show();
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



