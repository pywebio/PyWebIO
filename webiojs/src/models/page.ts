// page id to page window reference
import {Command, SubPageSession} from "../session";
import {LazyPromise} from "../utils";

let subpages: { [page_id: string]: Window } = {};


export function OpenPage(page_id: string) {
    if (page_id in subpages)
        throw `Can't open page, the page id "${page_id}" is duplicated`;
    subpages[page_id] = window.open(window.location.href);

    // the `_pywebio_page` will be resolved in new opened page in `SubPageSession.start_session()`
    // @ts-ignore
    subpages[page_id]._pywebio_page = new LazyPromise()
}

export function ClosePage(page_id: string) {
    if (!(page_id in subpages))
        throw `Can't close page, the page (id "${page_id}") is not found`;
    subpages[page_id].close()
}

export function DeliverMessage(msg: Command) {
    if (!(msg.page in subpages))
        throw `Can't deliver message, the page (id "${msg.page}") is not found`;
    // @ts-ignore
    subpages[msg.page]._pywebio_page.promise.then((page: SubPageSession) => {
        msg.page = undefined;
        page.server_message(msg);
    });
}