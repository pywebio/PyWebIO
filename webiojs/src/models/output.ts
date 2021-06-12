import {b64toBlob, randomid} from "../utils";
import * as marked from 'marked';
import {pushData} from "../session";
import {PinWidget} from "./pin";

export interface Widget {
    handle_type: string;

    get_element(spec: any): JQuery;  // The length of element must equal 1
}

let Text = {
    handle_type: 'text',
    get_element: function (spec: any): JQuery {
        let elem = spec.inline ? $('<span></span>') : $('<p></p>');
        elem.attr('style', 'white-space: pre-wrap;');
        elem.append(document.createTextNode(spec.content));
        return elem;
    }
};

marked.setOptions({
    breaks: true, //可行尾不加两空格直接换行
    smartLists: true,
    smartypants: false,
    mangle: false,
    highlight: function (code, lang, callback) {
        if (Prism.languages[lang]) {
            try {
                code = Prism.highlight(code, Prism.languages[lang]);
            } catch (e) {
                console.error('Prism highlight error:' + e)
            }
        }
        if (callback)
            return callback(null, code);
        else
            return code;
    },
});

let Markdown = {
    handle_type: 'markdown',
    get_element: function (spec: any) {
        // spec.options, see also https://marked.js.org/using_advanced#options
        let html_str = marked(spec.content, spec.options);
        if (spec.sanitize)
            try {
                html_str = DOMPurify.sanitize(html_str);
            } catch (e) {
                console.log('Sanitize html failed: %s\nHTML: \n%s', e, html_str);
            }
        return $(html_str);
    }
};

// 将html字符串解析成jQuery对象
function parseHtml(html_str: string) {
    let nodes = $.parseHTML(html_str, null, true);
    let elem;
    if (nodes.length != 1)
        elem = $(document.createElement('div')).append(nodes);
    else
        elem = $(nodes[0]);
    return elem;
}

let Html = {
    handle_type: 'html',
    get_element: function (spec: any) {
        let html_str = spec.content;
        if (spec.sanitize)
            try {
                html_str = DOMPurify.sanitize(html_str);
            } catch (e) {
                console.log('Sanitize html failed: %s\nHTML: \n%s', e, html_str);
            }
        return parseHtml(html_str);
    }
};

let Buttons = {
    handle_type: 'buttons',
    get_element: function (spec: any) {
        const btns_tpl = `<div{{#group}} class="btn-group" role="group"{{/group}}>{{#buttons}} 
                                <button class="btn {{#color}}btn-{{#outline}}outline-{{/outline}}{{color}}{{/color}}{{#small}} btn-sm{{/small}}">{{label}}</button> 
                          {{/buttons}}</div>`;
        spec.color = "primary";  // fallback color
        if (spec.link) {
            spec.outline = false;
            for (let btn of spec.buttons)
                btn.color = 'link';
        }

        let html = Mustache.render(btns_tpl, spec);
        let elem = $(html);

        let btns = elem.find('button');
        for (let idx = 0; idx < spec.buttons.length; idx++) {
            btns.eq(idx).on('click', (e) => {
                pushData(spec.buttons[idx].value, spec.callback_id);
            });
        }

        return elem;
    }
};

// 已废弃。为了向下兼容而保留
let File = {
    handle_type: 'file',
    get_element: function (spec: any) {
        const html = `<div><button type="button" class="btn btn-link">${spec.name}</button></div>`;
        let element = $(html);
        let blob = b64toBlob(spec.content);
        element.on('click', 'button', function (e) {
            saveAs(blob, spec.name, {}, false);
        });

        return element;
    }
};


let Table = {
    handle_type: 'table',
    get_element: function (spec: { data: any[][], span: { [i: string]: { col: number, row: number } } }) {
        const table_tpl = `
<table>
    <tr>
        {{#header}} 
        <th{{#col}} colspan="{{col}}"{{/col}}{{#row}} rowspan="{{row}}"{{/row}}>{{#content}}{{& pywebio_output_parse}}{{/content}}</th> 
        {{/header}}
    </tr>
      {{#tdata}} 
      <tr>
        {{# . }} 
        <td{{#col}} colspan="{{col}}"{{/col}}{{#row}} rowspan="{{row}}"{{/row}}>{{#content}}{{& pywebio_output_parse}}{{/content}}</td> 
        {{/ . }} 
      </tr>
      {{/tdata}}
    
</table>`;

        interface itemType {
            content: any, // spec of sub-output
            col?: number,
            row?: number
        }

        // 将spec转化成模版引擎的输入
        let table_data: itemType[][] = [];
        for (let row_id in spec.data) {
            table_data.push([]);
            let row = spec.data[row_id];
            for (let col_id in row) {
                let data = spec.data[row_id][col_id];

                // 处理简单类型单元格，即单元格不是output命令的spec
                if (typeof data !== 'object') {
                    data = {type: 'text', content: data, inline: true};
                }

                table_data[row_id].push({
                    content: data,
                    ...(spec.span[row_id + ',' + col_id] || {})
                });
            }
        }

        let header: itemType[], data: itemType[][];
        [header, ...data] = table_data;
        let html = render_tpl(table_tpl, {header: header, tdata: data});
        return $(html);
    }
};

const TABS_TPL = `<div class="webio-tabs">
{{#tabs}}
    <input type="radio" class="toggle" name="{{#uniqueid}}name{{/uniqueid}}" id="{{#uniqueid}}name{{/uniqueid}}{{index}}" {{#checked}}checked{{/checked}}>
    <label for="{{#uniqueid}}name{{/uniqueid}}{{index}}">{{title}}</label>
    <div class="webio-tabs-content">
    {{#content}}
        {{& pywebio_output_parse}}
    {{/content}}
    </div>
{{/tabs}}
</div>`;

let TabsWidget = {
    handle_type: 'tabs',
    get_element: function (spec: { tabs: { title: string, content: any, index: number, checked: boolean }[] }) {
        spec.tabs[0]['checked'] = true;
        for (let idx = 0; idx < spec.tabs.length; idx++) {
            spec.tabs[idx]['index'] = idx;
        }

        return render_tpl(TABS_TPL, spec);
    }
};

let CustomWidget = {
    handle_type: 'custom_widget',
    get_element: function (spec: { template: string, data: { [i: string]: any } }) {
        return render_tpl(spec.template, spec.data);
    }
};

let all_widgets: Widget[] = [Text, Markdown, Html, Buttons, File, Table, CustomWidget, TabsWidget, PinWidget];


let type2widget: { [i: string]: Widget } = {};
for (let w of all_widgets)
    type2widget[w.handle_type] = w;

export function getWidgetElement(spec: any) {
    if (!(spec.type in type2widget))
        throw Error("Unknown type in getWidgetElement() :" + spec.type);

    let elem = type2widget[spec.type].get_element(spec);
    if (spec.style) {
        // add style attribute
        let old_style = elem.attr('style') || '';
        elem.attr({"style": old_style + ';' + spec.style});
    }
    if (spec.container_dom_id) {
        if (spec.container_selector)
            elem.find(spec.container_selector).attr('id', spec.container_dom_id);
        else
            elem.attr('id', spec.container_dom_id);
    }
    return elem;
}


export function render_tpl(tpl: string, data: { [i: string]: any }) {
    let placeholder2spec: { [name: string]: any } = {};

    // {{#content}}{{& pywebio_output_parse}}{{/content}}
    data['pywebio_output_parse'] = function () {
        if (!this.type)
            return getWidgetElement({type: 'text', content: this, inline: true})[0].outerHTML;
        let dom_id = 'ph-' + randomid(10);
        placeholder2spec[dom_id] = this;
        return `<div id="${dom_id}"></div>`;
    };

    // {{#uniqueid}}name{{/uniqueid}}
    // {{uniqueid}}
    let names2id: { [name: string]: any } = {};
    data['uniqueid'] = function () {
        return function (name: string) {
            if (name) {
                if (!(name in names2id))
                    names2id[name] = 'webio-' + randomid(10);

                return names2id[name];
            } else {
                return 'webio-' + randomid(10);
            }
        };
    };

    // count the function call number
    // {{index}}
    let cnt = 0;
    data['index'] = function () {
        cnt += 1;
        return cnt;
    };

    let html = Mustache.render(tpl, data);
    let elem = parseHtml(html);
    for (let dom_id in placeholder2spec) {
        let spec = placeholder2spec[dom_id];
        let sub_elem = getWidgetElement(spec);
        elem.find(`#${dom_id}`).replaceWith(sub_elem);
    }
    return elem;
}