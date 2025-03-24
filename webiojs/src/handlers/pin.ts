import {ClientEvent, Command, Session} from "../session";
import {CommandHandler} from "./base";
import {GetPinValues, PinChangeCallback, PinUpdate, WaitChange, IsFileInput} from "../models/pin";
import {state} from "../state";
import {serialize_file, serialize_json} from "../utils";
import {t} from "../i18n";


export class PinHandler implements CommandHandler {
    session: Session;

    accept_command = ['pin_values', 'pin_update', 'pin_wait', 'pin_onchange'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        if (msg.command === 'pin_values') {
            let values = GetPinValues(msg.spec.names);
            let send_msg = {
                event: "js_yield", 
                task_id: msg.task_id,
                data: values
            };
            this.submit(
                send_msg, 
                msg.spec.names.filter(IsFileInput)
            );
        } else if (msg.command === 'pin_update') {
            PinUpdate(msg.spec.name, msg.spec.attributes);
        } else if (msg.command === 'pin_wait') {
            let p = WaitChange(msg.spec.names, msg.spec.timeout);
            Promise.resolve(p).then((change_info: (null | { name: string, value: any })) => {
                // change_info: null or {'name': name, 'value': value}
                let send_msg = {event: "js_yield", task_id: msg.task_id, data: change_info};
                this.submit(
                    send_msg, 
                    (change_info && IsFileInput(change_info.name)) ? ['value'] : []
                );
            }).catch((error) => {
                console.error('error in `pin_wait`: %s', error);
                this.submit({event: "js_yield", task_id: msg.task_id, data: null}, []);
            });
        } else if (msg.command === 'pin_onchange') {
            let onchange = (val: any) => {
                let send_msg = {
                    event: "callback",
                    task_id: msg.spec.callback_id,
                    data: {value: val}
                }
                this.submit(
                    send_msg, 
                    IsFileInput(msg.spec.name)? ['value'] : []
                );
            }
            PinChangeCallback(msg.spec.name, msg.spec.callback_id ? onchange : null, msg.spec.clear);
        }
    }

    /*
    * Send pin values to server.
    * `msg.data`: {input_name: input_value, ...} or null
    * for file input, the `input_value` is in {multiple: bool, files: File[] }
    * */
    submit(msg: ClientEvent, file_input_names: string[]) {
        // See: deserialize_binary_event() in pywebio/platform/utils.py
        let file_blobs:Blob[] = [];
        for (let name of file_input_names) {
            if (msg.data && msg.data[name]) {
                // {multiple: bool, files: File[]}
                let {multiple, files} = msg.data[name];
                msg.data[name] = multiple ? [] : null; // replace file value with initial value
                file_blobs.push(...files.map((file: File) => serialize_file(file, name)));
            }
        }

        if (file_blobs.length) {
            let toast = Toastify({
                text: `⏳${t("file_uploading")} 0%`,
                duration: -1,
                gravity: "top",
                position: 'center',
                backgroundColor: '#1565c0',
            });
            toast.showToast();
            state.CurrentSession.send_buffer(
                new Blob([serialize_json(msg), ...file_blobs], {type: 'application/octet-stream'}),
                (loaded: number, total: number) => {
                    toast.toastElement.innerText = `⏳${t("file_uploading")} ${((loaded / total)*100).toFixed(2)}%`;
                    if (total - loaded < 100) toast.hideToast();
                }
            );
        } else {
            state.CurrentSession.send_message(msg);
        }
    }
}