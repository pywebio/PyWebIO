import {Command} from "../session";
import {CommandHandler} from "./base";
import {state} from "../state";

export class ToastHandler implements CommandHandler {
    accept_command: string[] = ['toast'];

    constructor() {
    }

    handle_message(msg: Command) {
        let spec = msg.spec;
        let toast = Toastify({
            text: Mustache.escape(spec.content),
            duration: spec.duration === 0 ? -1 : spec.duration,  // -1 for permanent toast
            close: spec.duration === 0,//To show the close icon or not
            gravity: "top", // `top` or `bottom`
            position: spec.position, // `left`, `center` or `right`
            backgroundColor: spec.color,
            stopOnFocus: true, // Prevents dismissing of toast on hover
            onClick: function () {
                if (!spec.callback_id)
                    return;

                if (state.CurrentSession === null)
                    return console.error("Error: WebIOController is not instantiated");
                state.CurrentSession.send_message({
                    event: "callback",
                    task_id: spec.callback_id,
                    data: null
                });
                toast.hideToast();
            }
        });
        toast.showToast();
    }
}