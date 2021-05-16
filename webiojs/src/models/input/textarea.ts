import {InputItem} from "./base";
import {deep_copy, make_set} from "../../utils"
import {config as appConfig} from "../../state";


const textarea_input_tpl = `
<div class="form-group">
    {{#label}}<label for="{{id_name}}">{{label}}</label>{{/label}}
    <textarea id="{{id_name}}" aria-describedby="{{id_name}}_help" rows="{{rows}}" class="form-control" >{{value}}</textarea>
    <div class="invalid-feedback">{{invalid_feedback}}</div>  <!-- input 添加 is-invalid 类 -->
    <div class="valid-feedback">{{valid_feedback}}</div> <!-- input 添加 is-valid 类 -->
    <small id="{{id_name}}_help" class="form-text text-muted">{{help_text}}</small>
</div>`;


export class Textarea extends InputItem {
    static accept_input_types: string[] = ["textarea"];

    private code_mirror: any = null;
    private code_mirror_config: { [name: string]: any } = {
        'theme': 'base16-light',
        'mode': 'python',
        'lineNumbers': true,  // 显示行数
        'indentUnit': 4,  //缩进单位为4
        'styleActiveLine': true,  // 当前行背景高亮
        'matchBrackets': true,  //括号匹配
        'lineWrapping': true,  //自动换行
    };

    constructor(spec: any, task_id: string, on_input_event: (event_name: string, input_item: InputItem) => void) {
        super(spec, task_id, on_input_event);
    }

    create_element() {
        let that = this;

        let spec = deep_copy(this.spec);
        spec['id_name'] = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        let html = Mustache.render(textarea_input_tpl, spec);
        this.element = $(html);
        let input_elem = this.element.find('textarea');

        // blur事件时，发送当前值到服务器
        // input_elem.on('blur', this.send_value_listener);
        if (spec.onchange) {
            input_elem.on("input", (e) => {
                this.on_input_event("change", this);
            });
        }

        // 将额外的html参数加到input标签上
        const ignore_keys = make_set(['value', 'type', 'label', 'invalid_feedback', 'valid_feedback', 'help_text', 'rows', 'code']);
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }
        if (spec.code) {
            CodeMirror.modeURL = appConfig.codeMirrorModeURL;

            for (let k in that.spec.code)
                this.code_mirror_config[k] = that.spec.code[k];

            if (that.spec.readonly || that.spec.disabled)
                this.code_mirror_config['readOnly'] = "nocursor";

            if (this.code_mirror_config.theme && this.code_mirror_config.theme !== 'base16-light')
                Textarea.load_codemirror_theme(this.code_mirror_config.theme);
        }

        return this.element;
    };

    update_input(spec: any) {
        let attributes = spec.attributes;
        if (this.code_mirror && 'value' in attributes) {
            this.code_mirror.setValue(attributes['value']);
            delete attributes['value'];
        }

        this.update_input_helper.call(this, -1, attributes);
    };

    get_value() {
        if (this.code_mirror)
            return this.code_mirror.getValue();

        return this.element.find('textarea').val();
    };

    after_show(first_show: boolean): any {
        if (first_show && this.spec.code) {
            this.code_mirror = CodeMirror.fromTextArea(this.element.find('textarea')[0], this.code_mirror_config);
            try {
                CodeMirror.autoLoadMode(this.code_mirror, this.code_mirror_config.mode);
            } catch (e) {
                console.error('CodeMirror load mode `%s` error: %s', this.code_mirror_config.mode, e);
            }
            if (this.spec.onchange)
                this.code_mirror.on('change', (instance: object, changeObj: object) => {
                    this.on_input_event("change", this);
                })
            this.code_mirror.setSize(null, 20 * this.spec.rows);
        }
    };

    static load_codemirror_theme(theme: string, url_tpl = appConfig.codeMirrorThemeURL) {
        let cssId = 'codemirror_theme_' + theme;  // you could encode the css path itself to generate id..
        if (!document.getElementById(cssId)) {
            let head = document.getElementsByTagName('head')[0];
            let link = document.createElement('link');
            link.id = cssId;
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = url_tpl.replace('%N', theme);
            link.media = 'all';
            head.appendChild(link);
        }
    }
}



