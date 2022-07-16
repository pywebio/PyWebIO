// page id to page window reference
import {Command, SubPageSession} from "../session";
import {error_alert, LazyPromise} from "../utils";
import {state} from "../state";
import {t} from "../i18n";

let subpages: {
    [page_id: string]: {
        page: LazyPromise,
        task_id: string,
        session: LazyPromise,
        iframe: HTMLIFrameElement
    }
} = {};

function start_clean_up_task() {
    return setInterval(() => {
        for (let page_id in subpages) {
            subpages[page_id].page.promise.then((page: Window) => {
                if (page.closed || !SubPageSession.is_sub_page(page)) {
                    on_page_lost(page_id);
                }
            })
        }
    }, 1000)
}

// page is closed accidentally
function on_page_lost(page_id: string) {
    console.debug(`page ${page_id} exit`);
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

export function NotifyPageTerminate() {
    window.parent.postMessage({
        name: 'pywebio-page-close',
        // @ts-ignore
        page_id: window._pywebio_page_id
    }, "*");
}

window.addEventListener('message', event => {
    if (event.data.name == 'pywebio-page-close' && event.data.page_id) {
        let pid = event.data.page_id;
        if (!(pid in subpages))
            throw `Can't close page, the page (id "${pid}") is not found`;
        remove_iframe(subpages[pid].iframe);
        on_page_lost(pid);
    }
});

let clean_up_task_id: number = null;

export function OpenPageInNewWindow(page_id: string, task_id: string, parent_page: string) {
    if (page_id in subpages)
        throw `Can't open page, the page id "${page_id}" is duplicated`;

    if (!clean_up_task_id)
        clean_up_task_id = start_clean_up_task();

    // will be resolved as new opened page
    let page_promise = new LazyPromise()

    // will be resolved as SubPageSession in new opened page in `SubPageSession.start_session()`
    let page_session_promise = new LazyPromise()

    subpages[page_id] = {page: page_promise, task_id: task_id, session: page_session_promise, iframe: null}

    let page_open_task = (parent: Window) => {
        /*
        * Open new page and set up the page
        * */
        let page = parent.open(window.location.href);
        if (page == null) { // blocked by browser
            on_page_lost(page_id);
            return error_alert(t("page_blocked"));
        }
        // @ts-ignore
        page._pywebio_page = page_session_promise;
        // @ts-ignore
        page._master_window = window;
        // @ts-ignore
        page._pywebio_tasks = [];  // the task for sub-page
        page.addEventListener('message', event => {
            // @ts-ignore
            while (page._pywebio_tasks.length) {
                // @ts-ignore
                page._pywebio_tasks.shift()(page);  // pop first
            }
        });

        // this event is not reliably fired by browsers
        // https://developer.mozilla.org/en-US/docs/Web/API/Window/pagehide_event#usage_notes
        page.addEventListener('pagehide', event => {
            // wait some time to for `page.closed`
            setTimeout(() => {
                if (page.closed || !SubPageSession.is_sub_page(page))
                    on_page_lost(page_id)
            }, 100)
        });

        page_promise.resolve(page);
    }

    if (!parent_page) {
        page_open_task(window);
    } else {
        // open the new page in currently active page, otherwise, the opening action may be blocked by browser.
        subpages[parent_page].page.promise.then((opener: Window) => {
            // @ts-ignore
            opener._pywebio_tasks.push(page_open_task);

            // when opener receive this message, it will run the tasks in `opener._pywebio_tasks`
            opener.postMessage("", "*");
        });
    }
}

export function OpenPage(page_id: string, task_id: string, parent_page: string) {
    if (page_id in subpages)
        throw `Can't open page, the page id "${page_id}" is duplicated`;

    if (!clean_up_task_id)
        clean_up_task_id = start_clean_up_task();

    // will be resolved as new opened page
    let page_promise = new LazyPromise()

    // will be resolved as SubPageSession in new opened page in `SubPageSession.start_session()`
    let page_session_promise = new LazyPromise()

    subpages[page_id] = {page: page_promise, task_id: task_id, session: page_session_promise, iframe: null}

    let init_page = (page: Window) => {
        /*
        * Open new page and set up the page
        * */
        // let page = parent.open(window.location.href);
        if (page == null) { // blocked by browser
            on_page_lost(page_id);
            return error_alert(t("page_blocked"));
        }
        // @ts-ignore
        page._pywebio_page_id = page_id;
        // @ts-ignore
        page._pywebio_page = page_session_promise;
        // @ts-ignore
        page._master_window = window;
        // @ts-ignore
        page._pywebio_tasks = [];  // the task for sub-page
        page.addEventListener('message', event => {
            // @ts-ignore
            while (page._pywebio_tasks.length) {
                // @ts-ignore
                page._pywebio_tasks.shift()(page);  // pop first
            }
        });

        // this event is not reliably fired by browsers
        // https://developer.mozilla.org/en-US/docs/Web/API/Window/pagehide_event#usage_notes
        page.addEventListener('pagehide', event => {
            // wait some time to for `page.closed`
            setTimeout(() => {
                if (page.closed || !SubPageSession.is_sub_page(page))
                    on_page_lost(page_id)
            }, 100)
        });

        page_promise.resolve(page);
    }

    let iframe = document.createElement("iframe");
    subpages[page_id].iframe = iframe;
    iframe.classList.add('pywebio-page');
    iframe.src = location.href;
    iframe.frameBorder = "0";

    // show iframe
    $('body').append(iframe);
    init_page(iframe.contentWindow);
    setTimeout(() => {
        // show iframe
        iframe.classList.add('active');
        // disable the scrollbar in body
        document.documentElement.classList.add('overflow-y-hidden');
    }, 30);
}

function remove_iframe(iframe: HTMLIFrameElement) {
    iframe.classList.remove('active');
    setTimeout(() => {
        iframe.remove();
    }, 1000);

    if ($('body > .pywebio-page.active').length == 0)
        document.documentElement.classList.remove('overflow-y-hidden');
}

// close page by server
export function ClosePage(page_id: string) {
    if (!(page_id in subpages)) {
        throw `Can't close page, the page (id "${page_id}") is not found`;
    }
    subpages[page_id].page.promise.then((page: Window) => page.close());
    if (subpages[page_id].iframe != null) {
        remove_iframe(subpages[page_id].iframe)
    }
    delete subpages[page_id];
}

export function DeliverMessage(msg: Command) {
    if (!(msg.page in subpages))
        throw `Can't deliver message, the page (id "${msg.page}") is not found`;
    // @ts-ignore
    subpages[msg.page].session.promise.then((page: SubPageSession) => {
        msg.page = undefined;
        page.server_message(msg);
    });
}

export function CloseSession() {
    // close all subpage's session
    for (let page_id in subpages) {
        // @ts-ignore
        subpages[page_id].session.promise.then((page: SubPageSession) => {
            page.close_session()
        });
    }
}