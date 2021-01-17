import {Command} from "../session";
import {CommandHandler} from "./base";
import {b64toBlob} from "../utils";

export class DownloadHandler implements CommandHandler {
    accept_command: string[] = ['download'];

    constructor() {
    }

    handle_message(msg: Command) {
        let blob = b64toBlob(msg.spec.content);
        saveAs(blob, msg.spec.name, {}, false);
    }
}