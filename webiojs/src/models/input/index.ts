import {Input} from "./input"
import {Actions} from "./actions"
import {CheckboxRadio} from "./checkbox_radio"
import {Textarea} from "./textarea"
import {File} from "./file"
import {Select} from "./select"
import {Slider} from "./slider"
import {InputItem} from "./base";


export const all_input_items = [Input, Actions, CheckboxRadio, Textarea, File, Select, Slider];

export function get_input_item_from_type(type: string) {
    return type2item[type];
}

let type2item: { [t: string]: typeof InputItem } = {}
for (let item of all_input_items) {
    for (let t of item.accept_input_types)
        type2item[t] = item;
}
