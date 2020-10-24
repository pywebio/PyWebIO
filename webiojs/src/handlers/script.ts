import {Command, Session} from "../session";
import {CommandHandler} from "./base";


export class ScriptHandler implements CommandHandler {
    session: Session;

    accept_command = ['run_script'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        let script = msg.spec.code as string;
        let args = msg.spec.args as { [i: string]: any };
        let arg_names:string[] = ['WebIOCurrentTaskID'], arg_vals:any[] = [msg.task_id];
        for(let key in args){
            arg_names.push(key);
            arg_vals.push(args[key]);
        }
        const script_func = new Function(...arg_names, script);
        script_func(...arg_vals);
    }
}