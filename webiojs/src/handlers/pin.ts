import {ClientEvent, Command, Session} from "../session";
import {CommandHandler} from "./base";
import {GetPinValue, PinChangeCallback, PinUpdate, WaitChange, IsFileInput} from "../models/pin";
import {state} from "../state";
import {serialize_file, serialize_json} from "../utils";


export class PinHandler implements CommandHandler {
    session: Session;

    accept_command = ['pin_value', 'pin_update', 'pin_wait', 'pin_onchange'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        if (msg.command === 'pin_value') {
            let val = GetPinValue(msg.spec.name);  // undefined or value
            let send_msg = {
                event: "js_yield", task_id: msg.task_id,
                data: val === undefined ? null : {value: val}
            };
            this.submit(send_msg, IsFileInput(msg.spec.name));
        } else if (msg.command === 'pin_update') {
            PinUpdate(msg.spec.name, msg.spec.attributes);
        } else if (msg.command === 'pin_wait') {
            let p = WaitChange(msg.spec.names, msg.spec.timeout);
            Promise.resolve(p).then((change_info: (null | { name: string, value: any })) => {
                // change_info: null or {'name': name, 'value': value}
                let send_msg = {event: "js_yield", task_id: msg.task_id, data: change_info}
                this.submit(send_msg, IsFileInput(change_info.name));
            }).catch((error) => {
                console.error('error in `pin_wait`: %s', error);
                this.submit({event: "js_yield", task_id: msg.task_id, data: null});
            });
        } else if (msg.command === 'pin_onchange') {
            let onchange = (val: any) => {
                let send_msg = {
                    event: "callback",
                    task_id: msg.spec.callback_id,
                    data: {value: val}
                }
                this.submit(send_msg, IsFileInput(msg.spec.name));
            }
            PinChangeCallback(msg.spec.name, msg.spec.callback_id ? onchange : null, msg.spec.clear);
        }
    }

    /*
    * Send pin value to server.
    * `msg.data` may be null, or {value: any, ...}
    * `msg.data.value` stores the value of the pin.
    * when submit files, `msg.data.value` is {multiple: bool, files: File[] }
    * */
    submit(msg: ClientEvent, is_file: boolean = false) {
        if (is_file && msg.data !== null) {
            // msg.data.value: {multiple: bool, files: File[]}
            let {multiple, files} = msg.data.value;
            msg.data.value = multiple ? [] : null; // replace file value with initial value
            state.CurrentSession.send_buffer(
                new Blob([
                    serialize_json(msg),
                    ...files.map((file: File) => serialize_file(file, 'value'))
                ], {type: 'application/octet-stream'})
            );
        } else {
            state.CurrentSession.send_message(msg);
        }
    }
}