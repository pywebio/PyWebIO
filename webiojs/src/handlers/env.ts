import {Command, HttpSession} from "../session";
import {CommandHandler} from "./base";
import {config, state} from "../state";

export class EnvSettingHandler implements CommandHandler {
    accept_command: string[] = ['set_env'];

    constructor() {
    }

    handle_message(msg: Command) {
        let spec = msg.spec;
        if (spec.title !== undefined) {
            document.title = spec.title;
        }

        if (spec.auto_scroll_bottom !== undefined)
            state.AutoScrollBottom = spec.auto_scroll_bottom;

        if (spec.output_animation !== undefined) {
            config.outputAnimation = spec.output_animation;
        }

        if (spec.http_pull_interval !== undefined) {
            if (state.CurrentSession instanceof HttpSession)
                state.CurrentSession.change_pull_interval(spec.http_pull_interval);
        }
    }
}