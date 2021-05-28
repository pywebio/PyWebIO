import {Command, Session} from "../session";
import {config, state} from '../state'
import {body_scroll_to} from "../utils";

import {getWidgetElement} from "../models/output"
import {CommandHandler} from "./base";
import {AfterPinShow} from "../models/pin";

const DISPLAY_NONE_TAGS = ['script', 'style'];

export class OutputHandler implements CommandHandler {
    session: Session;

    accept_command = ['output', 'output_ctl'];

    private readonly container_parent: JQuery;
    private readonly container_elem: JQuery;

    constructor(session: Session, container_elem: JQuery) {
        this.session = session;
        this.container_elem = container_elem;
        this.container_parent = this.container_elem.parent();
    }

    scroll_bottom() {
        body_scroll_to($('.pywebio'), 'bottom', null, 15);
    };

    is_elem_visible(elem: JQuery) {
        try {
            return DISPLAY_NONE_TAGS.indexOf(elem[0].tagName.toLowerCase()) == -1;
        } catch (e) {
        }
        return false;
    }

    handle_message(msg: Command) {
        let output_to_root = false;
        if (msg.command === 'output') {
            let elem;
            try {
                elem = getWidgetElement(msg.spec);
            } catch (e) {
                return console.error(`Handle command error, command: ${msg}, error:${e}`);
            }

            let container_elem = $(msg.spec.scope);

            if (config.outputAnimation && this.is_elem_visible(elem) && container_elem.length == 1) elem.hide();

            if (container_elem.length === 0)
                return console.error(`Scope '${msg.spec.scope}' not found`);

            if (!msg.spec.scope || msg.spec.scope === '#pywebio-scope-ROOT') output_to_root = true;

            if (msg.spec.position === 0)
                container_elem.prepend(elem);
            else if (msg.spec.position === -1)
                container_elem.append(elem);
            else {
                for (let con of container_elem) {
                    let pos = $(con.children).eq(msg.spec.position);
                    if (msg.spec.position >= 0)
                        elem.insertBefore(pos);
                    else
                        elem.insertAfter(pos);
                }
            }

            if (this.is_elem_visible(elem) && container_elem.length == 1) {  // 输出内容为可见标签且输出目的scope唯一
                if (config.outputAnimation)
                    elem.fadeIn({
                        complete: () => {
                            // 当设置了AutoScrollBottom、并且当前输出输出到页面末尾时，滚动到底部
                            if (state.AutoScrollBottom && output_to_root)
                                this.scroll_bottom();
                        }
                    });
                else if (state.AutoScrollBottom && output_to_root)
                    this.scroll_bottom();
            }
            AfterPinShow();
        } else if (msg.command === 'output_ctl') {
            this.handle_output_ctl(msg);
        }
    };

    handle_output_ctl(msg: Command) {
        if (msg.spec.set_scope !== undefined) {
            let spec = msg.spec as {
                set_scope: string, // scope名
                container: string, // 此scope的父scope
                position: number, // 在父scope中创建此scope的位置 0 -> 在父scope的顶部创建, -1 -> 在父scope的尾部创建
                if_exist: string // 已经存在 ``name`` scope 时如何操作:  `'remove'` 表示先移除旧scope再创建新scope, `'clear'` 表示将旧scope的内容清除，不创建新scope，null/不指定时表示立即返回不进行任何操作
            };

            let container_elem = $(`${spec.container}`);
            if (container_elem.length === 0)
                return console.error(`Scope '${msg.spec.scope}' not found`);

            let old = $(`#${spec.set_scope}`);
            if (old.length) {
                if (spec.if_exist == 'remove')
                    old.remove();
                else if (spec.if_exist == 'clear') {
                    old.empty();
                    return;
                } else {
                    return;
                }
            }

            let html = `<div id="${spec.set_scope}"></div>`;
            if (spec.position === 0)
                container_elem.prepend(html);
            else if (spec.position === -1)
                container_elem.append(html);
            else {
                if (spec.position >= 0)
                    $(`${spec.container} > *`).eq(spec.position).insertBefore(html);
                else
                    $(`${spec.container} > *`).eq(spec.position).insertAfter(html);
            }
        }
        if (msg.spec.clear !== undefined) {
            $(msg.spec.clear).empty();
        }
        if (msg.spec.clear_before !== undefined)
            $(`${msg.spec.clear_before}`).prevAll().remove();
        if (msg.spec.clear_after !== undefined)
            $(`${msg.spec.clear_after} ~ *`).remove();
        if (msg.spec.scroll_to !== undefined) {
            let target = $(`${msg.spec.scroll_to}`);
            if (!target.length) {
                console.error(`Scope ${msg.spec.scroll_to} not found`);
            } else {
                body_scroll_to(target, msg.spec.position);
            }
        }
        if (msg.spec.clear_range !== undefined) {
            if ($(`${msg.spec.clear_range[0]}`).length &&
                $(`${msg.spec.clear_range[1]}`).length) {
                let removed: HTMLElement[] = [];
                let valid = false;
                $(`${msg.spec.clear_range[0]} ~ *`).each(function () {
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
            $(`${msg.spec.remove}`).remove();
    };

}
