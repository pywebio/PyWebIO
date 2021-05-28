import {Command, Session} from "../session";

import {render_tpl} from "../models/output"
import {CommandHandler} from "./base";
import {AfterPinShow} from "../models/pin";


export class PopupHandler implements CommandHandler {
    session: Session;

    accept_command = ['popup', 'close_popup'];

    private body = $('body');

    constructor(session: Session) {
        this.session = session;
    }

    static current_elem: JQuery<JQuery.Node> = null;  // 当前正在处于显示中的弹窗元素，表示页面的期望状态

    handle_message(msg: Command) {
        if (PopupHandler.current_elem) {
            // @ts-ignore
            PopupHandler.current_elem.modal('hide');
            PopupHandler.current_elem = null;
        }

        if (msg.command == 'popup') {
            // 显示弹窗前，先关闭其他弹窗
            // @ts-ignore
            $('.modal').modal('hide');

            let elem = PopupHandler.get_element(msg.spec);
            this.body.append(elem);
            AfterPinShow();

            // 弹窗关闭后就立即销毁
            elem.on('hidden.bs.modal', function (e) {
                elem.remove();
            });

            elem.on('shown.bs.modal', function (e) {
                // 弹窗显示后，有新弹窗出现或当前弹窗被关闭，则立即关闭当前弹窗
                if (elem != PopupHandler.current_elem || !PopupHandler.current_elem) {
                    // @ts-ignore
                    elem.modal('hide');
                }
            });

            // @ts-ignore
            elem.modal('show');
            PopupHandler.current_elem = elem;
        } else if (msg.command == 'close_popup') {
            // @ts-ignore
            $('.modal').modal('hide');
            PopupHandler.current_elem = null;
        }
    }

    static get_element(spec: { title: string, content: any[], closable: boolean, implicit_close: boolean, size: string }) {
        // https://v4.bootcss.com/docs/components/modal/#options
        const tpl = `<div class="modal fade" {{^implicit_close}}data-backdrop="static"{{/implicit_close}} aria-labelledby="model-id-{{ dom_id }}" tabindex="-1" role="dialog" aria-hidden="true">
          <div class="modal-dialog modal-dialog-scrollable {{#large}}modal-lg{{/large}} {{#small}}modal-sm{{/small}}" role="document">
            <div class="modal-content">
              <div class="modal-header">
                <h5 class="modal-title" id="model-id-{{ mid }}">{{ title }}</h5>
                {{#closable}}
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
                {{/closable}}
              </div>
              <div class="modal-body markdown-body" id="{{ dom_id }}">
                {{#content}}
                    {{& pywebio_output_parse}}
                {{/content}}
              </div>
              <!--  
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary">Submit</button>
              </div> 
              -->
            </div>
          </div>
        </div>`;

        if (!spec.closable)
            spec.implicit_close = false;

        return render_tpl(tpl, {
            ...spec,  // 字段： content, title, size, implicit_close, closable, dom_id
            large: spec.size == 'large',
            small: spec.size == 'small',
        });
    }

}