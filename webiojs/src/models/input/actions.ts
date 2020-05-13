import {Session} from "../../session";
import {InputItem} from "./base";

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

export class Actions extends InputItem {
    static accept_input_types: string[] = ["actions"];

    submit_value: string = null; // 提交表单时按钮组的value

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element(): JQuery {
        for (let b of this.spec.buttons) b['btn_type'] = b.type === "submit" ? "submit" : "button";

        const html = Mustache.render(buttons_tpl, this.spec);
        this.element = $(html);

        let that = this;
        this.element.find('button').on('click', function (e) {
            let btn = $(this);
            if (btn.data('type') === 'submit') {
                that.submit_value = btn.val() as string;
                // 不可以使用 btn.parents('form').submit()， 会导致input 的required属性失效
            } else if (btn.data('type') === 'reset') {
                btn.parents('form').trigger("reset");
            } else if (btn.data('type') === 'cancel') {
                that.session.send_message({
                    event: "from_cancel",
                    task_id: that.task_id,
                    data: null
                });
            } else {
                console.error("`actions` input: unknown button type '%s'", btn.data('type'));
            }
        });

        return this.element;
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        let idx = -1;
        if ('target_value' in spec) {
            this.element.find('button').each(function (index) {
                if ($(this).val() === spec.target_value) {
                    idx = index;
                    return false;
                }
            });
        }
        this.update_input_helper(idx, attributes);
    }

    get_value(): any {
        return this.submit_value;
    }
}



