import {Session} from "../../session";
import {InputItem} from "./base";
import {deep_copy} from "../../utils"
import {t} from "../../i18n";

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

    data_url_value: { filename: string, dataurl: string, mime_type: string, last_modified: number, size: number }[] = []; // 待上传文件信息
    valid = true;

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
            that.data_url_value = [];
            let total_size = 0;
            that.valid = true;
            let file = (input_elem[0] as HTMLInputElement).files;
            for (let f of file) {
                let fr = new FileReader();
                total_size += f.size;

                if (that.spec.max_size && f.size > that.spec.max_size) {
                    that.valid = false;
                    that.update_input_helper(-1, {
                        'valid_status': false,
                        'invalid_feedback': t("file_size_exceed", f.name, that._formate_size(that.spec.max_size)),
                    });
                } else if (that.spec.max_total_size && total_size > that.spec.max_total_size) {
                    that.valid = false;
                    that.update_input_helper(-1, {
                        'valid_status': false,
                        'invalid_feedback': t("file_total_size_exceed",that._formate_size(that.spec.max_total_size))
                    });
                    return;
                }
                if (!that.valid) return;
                that.update_input_helper(-1, {'valid_status': 0});

                fr.onload = function () {
                    that.data_url_value.push({
                        'filename': f.name,
                        'size': f.size,
                        'mime_type': f.type,
                        'last_modified': f.lastModified / 1000,
                        'dataurl': fr.result as string
                    });
                };
                fr.readAsDataURL(f);
            }

        });

        return this.element;
    }

    _formate_size(size: number): string {
        for (let s of ['Byte', 'Kb', 'Mb']) {
            if (size / 1024 < 1)
                return size.toFixed(2) + s;
            size = size / 1024;
        }
        return size.toFixed(2) + 'Gb';
    }

    update_input(spec: any): any {
        let attributes = spec.attributes;
        this.update_input_helper(-1, attributes);
    }

    check_valid(): boolean {
        return this.valid;
    }

    get_value(): any {
        return this.data_url_value;
    }

    after_add_to_dom(): any {
        bsCustomFileInput.init();
    }
}



