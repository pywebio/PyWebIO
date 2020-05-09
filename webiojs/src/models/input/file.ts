import {Session} from "../../session";
import {InputItem} from "./base";
import {deep_copy} from "../../utils"
import {state} from "../../state";

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

export class File extends InputItem {
    static accept_input_types: string[] = ["file"];

    data_url_value: { filename: string, dataurl: string } = null; // 待上传文件信息

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element(): JQuery {
        let spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;

        const html = Mustache.render(file_input_tpl, spec);
        this.element = $(html);
        let input_elem = this.element.find('input[type="file"]');

        const ignore_keys = {
            'label': '',
            'invalid_feedback': '',
            'valid_feedback': '',
            'help_text': '',
            'placeholder': ''
        };
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }

        // 文件选中后先不通知后端
        let that = this;
        input_elem.on('change', function () {
            let file = (input_elem[0] as HTMLInputElement).files[0];
            let fr = new FileReader();
            fr.onload = function () {
                that.data_url_value = {
                    'filename': file.name,
                    'dataurl': fr.result as string
                };
                console.log(that.data_url_value);
            };
            fr.readAsDataURL(file);
        });
        //  todo 通过回调的方式调用init
        setTimeout(bsCustomFileInput.init, state.ShowDuration + 100);

        return this.element;
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        this.update_input_helper(-1, attributes);
    }

    get_value(): any {
        return this.data_url_value;
    }
}



