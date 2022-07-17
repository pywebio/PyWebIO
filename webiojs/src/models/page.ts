// page id to page window reference
import {Command, SubPageSession} from "../session";
import {error_alert, LazyPromise} from "../utils";
import {state} from "../state";
import {t} from "../i18n";

let subpages: {
    [page_id: string]: SubPage
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

export declare type PageArgs = {
    page_id: String,
    page_session: LazyPromise<SubPageSession>,
    master_window: Window,
    on_terminate: () => void,
};

// export declare let _pywebio_page_args: PageArgs;

class SubPage {
    page: LazyPromise<Window>
    task_id: string
    session: LazyPromise<SubPageSession>
    iframe: HTMLIFrameElement

    private page_id: string;
    private new_window: boolean;
    private page_tasks: ((w: Window) => void)[];

    /*
    * new_window: whether to open sub-page as new browser window or iframe
    * */
    constructor(args: { page_id: string, task_id: string, parent: SubPage, new_window: boolean }) {
        // will be resolved as new opened page
        this.page = new LazyPromise<Window>();
        // will be resolved as SubPageSession in new opened page in `SubPageSession.start_session()`
        this.session = new LazyPromise<SubPageSession>();
        this.task_id = args.task_id;

        this.page_id = args.page_id;
        this.new_window = args.new_window;
        this.page_tasks = [];
    }

    start() {
        if (this.new_window) { // open sub-page in new browser window


        } else { // open sub-page as iframe
            this.iframe = SubPage.build_iframe();
            this.init_page(this.iframe.contentWindow);
        }
    }

    static build_iframe() {
        let iframe = document.createElement("iframe");
        iframe.classList.add('pywebio-page');
        iframe.src = location.href;
        iframe.frameBorder = "0";

        // show iframe
        $('body').append(iframe);
        // must after the iframe is appended to DOM
        setTimeout(() => {
            // show iframe
            iframe.classList.add('active');
            // disable the scrollbar in body
            document.documentElement.classList.add('overflow-y-hidden');
        }, 30);

        return iframe;
    }

    static remove_iframe(iframe: HTMLIFrameElement) {
        iframe.classList.remove('active');
        setTimeout(() => {
            iframe.remove();
        }, 1000);

        if ($('body > .pywebio-page.active').length == 0)
            document.documentElement.classList.remove('overflow-y-hidden');
    }

    /*
    * set up the page
    * */
    private init_page(page: Window) {
        if (page == null) { // blocked by browser
            on_page_lost(this.page_id);
            return error_alert(t("page_blocked"));
        }

        let args: PageArgs = {
            page_id: this.page_id,
            page_session: this.session,
            master_window: window,
            on_terminate: () => {
                SubPage.remove_iframe(subpages[this.page_id].iframe);
                on_page_lost(this.page_id);
            }
        }
        // @ts-ignore
        page._pywebio_page_args = args;

        page.addEventListener('message', event => {
            while (this.page_tasks.length) {
                this.page_tasks.shift()(page);  // pop first
            }
        });

        this.page.resolve(page);
    }

    close(){
        if(this.new_window){
            this.page.promise.then((page: Window) => page.close());
        }else{
            SubPage.remove_iframe(this.iframe)
        }
    }
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

let clean_up_task_id: number = null;

export function OpenPage(page_id: string, task_id: string, parent_page: string) {
    if (page_id in subpages)
        throw `Can't open page, the page id "${page_id}" is duplicated`;

    if (!clean_up_task_id)
        clean_up_task_id = start_clean_up_task();

    let parent = null;
    if (parent_page)
        parent = subpages[parent_page];

    let page = new SubPage({
        page_id: page_id,
        task_id: task_id,
        parent: parent,
        new_window: false,
    });
    subpages[page_id] = page;
    page.start()
}


// close page by server
export function ClosePage(page_id: string) {
    if (!(page_id in subpages)) {
        throw `Can't close page, the page (id "${page_id}") is not found`;
    }
    subpages[page_id].close();
    delete subpages[page_id];
}

export function DeliverMessage(msg: Command) {
    if (!(msg.page in subpages))
        throw `Can't deliver message, the page (id "${msg.page}") is not found`;
    subpages[msg.page].session.promise.then((page: SubPageSession) => {
        msg.page = undefined;
        page.server_message(msg);
    });
}

// close all subpage's session
export function CloseSession() {
    for (let page_id in subpages) {
        subpages[page_id].session.promise.then((page: SubPageSession) => {
            page.close_session()
        });
    }
}