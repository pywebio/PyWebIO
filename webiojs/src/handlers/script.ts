import {Command, Session} from "../session";
import {CommandHandler} from "./base";


export class ScriptHandler implements CommandHandler {
    session: Session;

    accept_command = ['run_script'];

    constructor(session: Session) {
        this.session = session;
    }

    handle_message(msg: Command) {
        let script = msg.spec as string;
        const script_func = new Function('WebIOCurrentTaskID', script);
        script_func(msg.task_id);
    }
}