import {Command, Session} from "../session";
import {randomid} from "../utils";

import {getWidgetElement} from "../models/output"
import {CommandHandler} from "./base";


export class PopupHandler implements CommandHandler{
    session: Session;

    accept_command = ['popup', 'close_popup'];

    private body = $('body');

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        if (msg.command == 'popup') {
            let ele = PopupHandler.get_element(msg.spec);
            this.body.append(ele);
            ele.on('hidden.bs.modal', function (e) {
                ele.remove();
            });
            // @ts-ignore
            ele.modal('show');
        } else if (msg.command == 'close_popup') {
            // @ts-ignore
            $('.modal').modal('hide');
        }
    }

    static get_element(spec: { title: string, content: any[], closable: boolean, implicit_close: boolean, size: string }) {
        // https://v4.bootcss.com/docs/components/modal/#options
        const tpl = `<div class="modal fade" {{^implicit_close}}data-backdrop="static"{{/implicit_close}} aria-labelledby="model-id-{{ mid }}" tabindex="-1" role="dialog" aria-hidden="true">
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
              <div class="modal-body markdown-body">
                {{& content }}
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
        let mid = randomid(10);

        let body_html = '';

        for (let output_item of spec.content) {
            if (typeof output_item === 'object') {
                try {
                    let nodes = getWidgetElement(output_item);
                    for (let node of nodes)
                        body_html += node.outerHTML || '';
                } catch (e) {
                    console.error('Get widget html error,', e, output_item);
                }
            } else {
                body_html += output_item;
            }
        }

        if (!spec.closable)
            spec.implicit_close = false;

        let html = Mustache.render(tpl, {
            ...spec,  // 字段： content, title, size, implicit_close, closable
            large: spec.size == 'large',
            small: spec.size == 'small',
            mid: mid,
            content: body_html,
        });
        return $(html as string);
    }

}