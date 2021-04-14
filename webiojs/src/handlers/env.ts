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

        if (spec.input_panel_min_height !== undefined) {
            state.InputPanelMinHeight = spec.input_panel_min_height;
        }

        if (spec.input_panel_init_height !== undefined) {
            state.InputPanelInitHeight = spec.input_panel_init_height;
        }

        if(spec.input_panel_fixed !== undefined){
            state.FixedInputPanel =  spec.input_panel_fixed;
        }

        if(spec.input_auto_focus !== undefined){
            state.AutoFocusOnInput =  spec.input_auto_focus;
        }
    }
}