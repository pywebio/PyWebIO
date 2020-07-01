import {InputItem} from "./base";
import {Session} from "../../session";
import {deep_copy, make_set} from "../../utils"
import {config as appConfig, state} from "../../state";


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

    constructor(session: Session, task_id: string, spec: any) {
        super(session, task_id, spec);
    }

    create_element() {
        let that = this;

        let spec = deep_copy(this.spec);
        const id_name = spec.name + '-' + Math.floor(Math.random() * Math.floor(9999));
        spec['id_name'] = id_name;
        let html = Mustache.render(textarea_input_tpl, spec);
        this.element = $(html);
        let input_elem = this.element.find('#' + id_name);

        // blur事件时，发送当前值到服务器
        // input_elem.on('blur', this.send_value_listener);

        // 将额外的html参数加到input标签上
        const ignore_keys = make_set(['value', 'type', 'label', 'invalid_feedback', 'valid_feedback', 'help_text', 'rows', 'code']);
        for (let key in this.spec) {
            if (key in ignore_keys) continue;
            input_elem.attr(key, this.spec[key]);
        }
        if (spec.code) {
            CodeMirror.modeURL = appConfig.codeMirrorModeURL;

            let config: { [name: string]: any } = {
                'theme': 'base16-light',
                'mode': 'python',
                'lineNumbers': true,  // 显示行数
                'indentUnit': 4,  //缩进单位为4
                'styleActiveLine': true,  // 当前行背景高亮
                'matchBrackets': true,  //括号匹配
                'lineWrapping': true,  //自动换行
            };
            for (let k in that.spec.code)
                config[k] = that.spec.code[k];

            if (config.theme && config.theme !== 'base16-light')
                Textarea.load_codemirror_theme(config.theme);

            setTimeout(function () {  // 需要等待当前表单被添加到文档树中后，再初始化CodeMirror，否则CodeMirror样式会发生错误
                that.code_mirror = CodeMirror.fromTextArea(that.element.find('textarea')[0], config);
                CodeMirror.autoLoadMode(that.code_mirror, config.mode);
                that.code_mirror.setSize(null, 20 * that.spec.rows);
            }, 100);

            setTimeout(function () {  // 需要等待当前表单显示后，重新计算表单高度
                // 重新计算表单高度
                that.element.parents('.card').height('auto');
            }, state.ShowDuration+40);
        }

        return this.element;
    };

    update_input(spec: any) {
        let attributes = spec.attributes;

        this.update_input_helper.call(this, -1, attributes);
    };

    get_value() {
        return this.element.find('textarea').val();
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



