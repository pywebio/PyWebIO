// page id to page window reference
import {Command, SubPageSession} from "../session";
import {LazyPromise} from "../utils";
import {state} from "../state";

let subpages: {
    [page_id: string]: {
        page: Window,
        task_id: string
    }
} = {};

function start_clean_up_task() {
    return setInterval(() => {
        let page;
        for (let page_id in subpages) {
            page = subpages[page_id].page;
            if (page.closed || !SubPageSession.is_sub_page(page)) {
                on_page_lost(page_id);
            }
        }
    }, 1000)
}

// page is closed accidentally
function on_page_lost(page_id: string) {
    console.log(`page ${page_id} exit`);
    if (!(page_id in subpages))  // it's a duplicated call
        return;

    let task_id = subpages[page_id].task_id;
    delete subpages[page_id];
    state.CurrentSession.send_message({
        event: "page_close",
        task_id: task_id,
        data: page_id
    });
}

let clean_up_task_id: number = null;

export function OpenPage(page_id: string, task_id: string) {
    if (page_id in subpages)
        throw `Can't open page, the page id "${page_id}" is duplicated`;

    if (!clean_up_task_id)
        clean_up_task_id = start_clean_up_task()

    let page = window.open(window.location.href);
    subpages[page_id] = {page: page, task_id: task_id}

    // the `_pywebio_page` will be resolved in new opened page in `SubPageSession.start_session()`
    // @ts-ignore
    page._pywebio_page = new LazyPromise()

    // this event is not reliably fired by browsers
    // https://developer.mozilla.org/en-US/docs/Web/API/Window/pagehide_event#usage_notes
    page.addEventListener('pagehide', event => {
        // wait some time to for `page.closed`
        setTimeout(() => {
            if (page.closed || !SubPageSession.is_sub_page(page))
                on_page_lost(page_id)
        }, 100)
    });
}

export function ClosePage(page_id: string) {
    if (!(page_id in subpages))
        throw `Can't close page, the page (id "${page_id}") is not found`;
    subpages[page_id].page.close();
    delete subpages[page_id];
}

export function DeliverMessage(msg: Command) {
    if (!(msg.page in subpages))
        throw `Can't deliver message, the page (id "${msg.page}") is not found`;
    // @ts-ignore
    subpages[msg.page].page._pywebio_page.promise.then((page: SubPageSession) => {
        msg.page = undefined;
        page.server_message(msg);
    });
}