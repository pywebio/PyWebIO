import {get_input_item_from_type} from "./input/index"
import {InputItem} from "./input/base";
import {error_alert} from "../utils";
import {t} from "../i18n";

let after_show_callbacks: (() => void) [] = [];

export function AfterPinShow() {
    for (let cb of after_show_callbacks) {
        try {
            cb.call(this);
        } catch (e) {
            console.error('Error in callback of pin widget show event.');
        }
    }
    after_show_callbacks = [];
}

let name2input: { [k: string]: InputItem } = {};

export function GetPinValue(name: string) {
    return name2input[name].get_value();
}

export function PinUpdate(name: string, attributes: { [k: string]: any }) {
    name2input[name].update_input({attributes:attributes});
}

let onchange_callbacks: { [name: string]: ((val: any) => void)[] } = {}; // name->[]

export function WaitChange(names: string[]) {
    let promises = [];
    for (let name of names) {
        if (!(name in onchange_callbacks))
            onchange_callbacks[name] = [];

        promises.push(new Promise(resolve => {
            onchange_callbacks[name].push(value => {
                resolve({'name': name, 'value': value})
            });
        }));
    }
    return Promise.race(promises);
}

function trigger_onchange_event(name: string, value: any) {
    let resolve_list = onchange_callbacks[name] || [];
    for (let resolve of resolve_list)
        resolve(value);
}

export let PinWidget = {
    handle_type: 'pin',
    get_element: function (spec: any) {
        let input_spec = spec.input;
        if(input_spec.name in name2input){
            let tip = `<p style="color: grey; border:1px solid #ced4da; padding: .375rem .75rem;">${t("duplicated_pin_name")}</p>`;
            name2input[input_spec.name].element.replaceWith(tip);
        }

        input_spec.onchange = true;
        input_spec.onblur = true;
        let InputClass = get_input_item_from_type(input_spec.type);
        let input_item = new InputClass(input_spec, null, (event, input_item) => {
            if(event=='change')
                trigger_onchange_event(input_spec.name, input_item.get_value());
        });

        name2input[input_spec.name] = input_item;

        after_show_callbacks.push(() => {
            input_item.after_add_to_dom();
            input_item.after_show(true);
        });

        return input_item.create_element();
    }
};


