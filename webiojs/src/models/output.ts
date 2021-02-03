import {b64toBlob} from "../utils";
import * as marked from 'marked';

/*
* 当前限制
* 若Widget被作为其他Widget的子项时，该Widget中绑定的事件将会失效
* */

export interface Widget {
    handle_type: string;

    get_element(spec: any): JQuery;
}

let Text = {
    handle_type: 'text',
    get_element: function (spec: any): JQuery {
        let elem = spec.inline ? $('<span></span>') : $('<p></p>');
        spec.content = spec.content.replace(/ /g, '\u00A0');
        // make '\n' to <br/>
        let lines = (spec.content || '').split('\n');
        for (let idx = 0; idx < lines.length - 1; idx++)
            elem.append(document.createTextNode(lines[idx])).append('<br/>');
        elem.append(document.createTextNode(lines[lines.length - 1]));
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
        const btns_tpl = `<div>{{#buttons}} 
                                <button class="btn {{#color}}btn-{{color}}{{/color}}{{#small}} btn-sm{{/small}}">{{label}}</button> 
                          {{/buttons}}</div>`;
        spec.color = spec.link ? "link" : "primary";
        let html = Mustache.render(btns_tpl, spec);
        let elem = $(html);

        let btns = elem.find('button');
        for (let idx = 0; idx < spec.buttons.length; idx++) {
            // note： 若Buttons被作为其他Widget的子项时，Buttons中绑定的事件将会失效，所以使用onclick attr设置点击事件
            btns.eq(idx).attr('onclick', `WebIO.pushData(${JSON.stringify(spec.buttons[idx].value)}, "${spec.callback_id}")`);
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
        <th{{#col}} colspan="{{col}}"{{/col}}{{#row}} rowspan="{{row}}"{{/row}}>{{& data}}</th> 
        {{/header}}
    </tr>
      {{#tdata}} 
      <tr>
        {{# . }} 
        <td{{#col}} colspan="{{col}}"{{/col}}{{#row}} rowspan="{{row}}"{{/row}}>{{& data}}</td> 
        {{/ . }} 
      </tr>
      {{/tdata}}
    
</table>`;

        interface itemType {
            data: string,
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
                    data: outputSpecToHtml(data),
                    ...(spec.span[row_id + ',' + col_id] || {})
                });
            }
        }

        let header: itemType[], data: itemType[][];
        [header, ...data] = table_data;
        let html = Mustache.render(table_tpl, {header: header, tdata: data});
        return $(html);
    }
};

let CustomWidget = {
    handle_type: 'custom_widget',
    get_element: function (spec: { template: string, data: { [i: string]: any } }) {
        spec.data['pywebio_output_parse'] = function () {
            if (this.type)
                return outputSpecToHtml(this);
            else
                return outputSpecToHtml({type: 'text', content: this, inline: true});
        };
        let html = Mustache.render(spec.template, spec.data);
        return parseHtml(html);
    }
};

let all_widgets: Widget[] = [Text, Markdown, Html, Buttons, File, Table, CustomWidget];


let type2widget: { [i: string]: Widget } = {};
for (let w of all_widgets)
    type2widget[w.handle_type] = w;

export function getWidgetElement(spec: any) {
    if (!(spec.type in type2widget))
        throw Error("Unknown type in getWidgetElement() :" + spec.type);

    let elem = type2widget[spec.type].get_element(spec);
    if (spec.style) {
        let old_style = elem.attr('style') || '';
        elem.attr({"style": old_style + spec.style});
    }
    return elem;
}

// 将output指令的spec字段解析成html字符串
export function outputSpecToHtml(spec: any) {
    let html = '';
    try {
        let nodes = getWidgetElement(spec);
        for (let node of nodes)
            html += node.outerHTML || '';
    } catch (e) {
        console.error('Get sub widget html error,', e, spec);
    }
    return html;
}


