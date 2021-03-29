import {Command, Session} from "../session";
import {CommandHandler} from "./base";
import {state} from "../state";


export class ScriptHandler implements CommandHandler {
    session: Session;

    accept_command = ['run_script'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        let script = msg.spec.code as string;
        let args = msg.spec.args as { [i: string]: any };

        let arg_names: string[] = [];
        let arg_vals: any[] = [];

        for (let key in args) {
            arg_names.push(key);
            arg_vals.push(args[key]);
        }

        let res = null;
        script = `return eval(${JSON.stringify(script)})`;  // lgtm [js/bad-code-sanitization]
        try {
            const script_func = new Function(...arg_names, script);
            res = script_func(...arg_vals);
        } catch (e) {
            console.log('Exception occurred in user code of `run_script` command: \n%s', e);
        }
        if (msg.spec.eval) {
            // credit: https://stackoverflow.com/questions/27746304/how-do-i-tell-if-an-object-is-a-promise
            Promise.resolve(res).then(function (value) {
                state.CurrentSession.send_message({event: "js_yield", task_id: msg.task_id, data: value || null});
            }).catch((error) => {
                state.CurrentSession.send_message({event: "js_yield", task_id: msg.task_id, data: null});
            });
        }
    }
}