import {state} from '../state'
import {b64toBlob} from "../utils";

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

let _md_parser = new Mditor.Parser();
let Markdown = {
    handle_type: 'markdown',
    get_element: function (spec: any) {
        return $(_md_parser.parse(spec.content));
    }
};

let Html = {
    handle_type: 'html',
    get_element: function (spec: any) {
        let nodes = $.parseHTML(spec.content, null, true);
        let elem = $(nodes) as any;
        if (nodes.length > 1)
            elem = $('<div><div/>').append(nodes);
        return elem;
    }
};

let Buttons = {
    handle_type: 'buttons',
    get_element: function (spec: any) {
        const btns_tpl = `<div class="form-group">{{#buttons}}
                             <button value="{{value}}" onclick="WebIO.DisplayAreaButtonOnClick(this, '{{callback_id}}')" class="btn btn-primary {{#small}}btn-sm{{/small}}">{{label}}</button> 
                          {{/buttons}}</div>`;
        let html = Mustache.render(btns_tpl, spec);
        return $(html);
    }
};

// 显示区按钮点击回调函数
export function DisplayAreaButtonOnClick(this_ele: HTMLElement, callback_id: string) {
    if (state.CurrentSession === null)
        return console.error("can't invoke DisplayAreaButtonOnClick when WebIOController is not instantiated");

    if (state.CurrentSession.closed())
        return alert("与服务器连接已断开，请刷新页面重新操作");

    let val = $(this_ele).val();
    state.CurrentSession.send_message({
        event: "callback",
        task_id: callback_id,
        data: val
    });
}

let File = {
    handle_type: 'file',
    get_element: function (spec: any) {
        const html = `<div class="form-group"><button type="button" class="btn btn-link">${spec.name}</button></div>`;
        let element = $(html);
        let blob = b64toBlob(spec.content);
        element.on('click', 'button', function (e) {
            saveAs(blob, spec.name, {}, false);
        });

        return element;
    }
};


export let all_widgets: Widget[] = [Text, Markdown, Html, Buttons, File];