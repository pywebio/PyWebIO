import {Command} from "../session";
import {CommandHandler} from "./base";
import {ClosePage, OpenPage} from "../models/page";

export class PageHandler implements CommandHandler {
    accept_command: string[] = ['open_page', 'close_page'];

    constructor() {
    }

    handle_message(msg: Command) {
        if (msg.command === 'open_page') {
            OpenPage(msg.spec.page_id, msg.task_id);
        } else if (msg.command === 'close_page') {
            ClosePage(msg.spec.page_id);
        }
    }
}