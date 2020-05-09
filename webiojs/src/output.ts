import {Command, Session} from "./session";
import {config, state} from './state'
import {body_scroll_to, box_scroll_to} from "./utils";

import {all_widgets, Widget} from "./models/output"


export class OutputController {
    session: Session;
    md_parser = new Mditor.Parser();


    static accept_command = ['output', 'output_ctl'];
    static widgets: { [i: string]: Widget } = {};

    private body = $('html,body');
    private readonly container_parent: JQuery;
    private readonly container_elem: JQuery;

    static add_widget(w: Widget) {
        this.widgets[w.handle_type] = w;
    }

    constructor(session: Session, container_elem: JQuery) {
        this.session = session;
        this.container_elem = container_elem;
        this.container_parent = this.container_elem.parent();
    }

    scroll_bottom() {
        // 固定高度窗口滚动
        if (state.OutputFixedHeight)
            box_scroll_to(this.container_elem, this.container_parent, 'bottom', undefined, 30);
        // 整个页面自动滚动
        body_scroll_to(this.container_parent, 'bottom');
    };

    handle_message(msg: Command) {
        let scroll_bottom = false;
        if (msg.command === 'output') {
            const output_type = msg.spec.type;
            if (!(output_type in OutputController.widgets)) {
                return console.error('Unknown output type:%s', msg.spec.type);
            }

            let elem = OutputController.widgets[msg.spec.type].get_element(msg.spec);
            if (config.outputAnimation) elem.hide();
            if (msg.spec.anchor !== undefined && this.container_elem.find(`#${msg.spec.anchor}`).length) {
                let pos = this.container_elem.find(`#${msg.spec.anchor}`);
                pos.empty().append(elem);
                elem.unwrap().attr('id', msg.spec.anchor);
            } else {
                if (msg.spec.anchor !== undefined)
                    elem.attr('id', msg.spec.anchor);

                if (msg.spec.before !== undefined) {
                    this.container_elem.find('#' + msg.spec.before).before(elem);
                } else if (msg.spec.after !== undefined) {
                    this.container_elem.find('#' + msg.spec.after).after(elem);
                } else {
                    this.container_elem.append(elem);
                    scroll_bottom = true;
                }
            }
            if (config.outputAnimation) elem.fadeIn();
        } else if (msg.command === 'output_ctl') {
            this.handle_output_ctl(msg);
        }
        // 当设置了AutoScrollBottom、并且当前输出输出到页面末尾时，滚动到底部
        if (state.AutoScrollBottom && scroll_bottom)
            this.scroll_bottom();
    };

    handle_output_ctl(msg: Command) {
        if (msg.spec.title) {
            $('#title').text(msg.spec.title);  // 直接使用#title不规范 todo
            document.title = msg.spec.title;
        }
        if (msg.spec.output_fixed_height !== undefined) {
            state.OutputFixedHeight = msg.spec.output_fixed_height;
            if (msg.spec.output_fixed_height)
                $('.container').removeClass('no-fix-height');  // todo 不规范
            else
                $('.container').addClass('no-fix-height');  // todo 不规范
        }
        if (msg.spec.auto_scroll_bottom !== undefined)
            state.AutoScrollBottom = msg.spec.auto_scroll_bottom;
        if (msg.spec.set_anchor !== undefined) {
            this.container_elem.find(`#${msg.spec.set_anchor}`).removeAttr('id');
            this.container_elem.append(`<div id="${msg.spec.set_anchor}"></div>`);
            // if (this.container_elem.find(`#${msg.spec.set_anchor}`).length === 0)
            //     this.container_elem.append(`<div id="${msg.spec.set_anchor}"></div>`);
        }
        if (msg.spec.clear_before !== undefined)
            this.container_elem.find(`#${msg.spec.clear_before}`).prevAll().remove();
        if (msg.spec.clear_after !== undefined)
            this.container_elem.find(`#${msg.spec.clear_after}~*`).remove();
        if (msg.spec.scroll_to !== undefined) {
            let target = $(`#${msg.spec.scroll_to}`);
            if (!target.length) {
                console.error(`Anchor ${msg.spec.scroll_to} not found`);
            } else if (state.OutputFixedHeight) {
                box_scroll_to(target, this.container_parent, msg.spec.position);
            } else {
                body_scroll_to(target, msg.spec.position);
            }
        }
        if (msg.spec.clear_range !== undefined) {
            if (this.container_elem.find(`#${msg.spec.clear_range[0]}`).length &&
                this.container_elem.find(`#${msg.spec.clear_range[1]}`).length) {
                let removed: HTMLElement[] = [];
                let valid = false;
                this.container_elem.find(`#${msg.spec.clear_range[0]}~*`).each(function () {
                    if (this.id === msg.spec.clear_range[1]) {
                        valid = true;
                        return false;
                    }
                    removed.push(this);
                    // $(this).remove();
                });
                if (valid)
                    $(removed).remove();
                else
                    console.warn(`clear_range not valid: can't find ${msg.spec.clear_range[1]} after ${msg.spec.clear_range[0]}`);
            }
        }
        if (msg.spec.remove !== undefined)
            this.container_elem.find(`#${msg.spec.remove}`).remove();
    };

}


for (let widget of all_widgets)
    OutputController.add_widget(widget);