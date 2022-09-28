import {error_alert} from "./utils";
import {state} from "./state";
import {t} from "./i18n";
import {CloseSession} from "./models/page";
import {PageArgs} from "./models/page";

export interface Command {
    command: string
    task_id: string
    page: string,
    spec: any
}

export interface ClientEvent {
    event: string,
    task_id: string,
    data: any
}


/*
* 会话
* 向外暴露的事件：on_session_create、on_session_close、on_server_message
* 提供的函数：start_session、send_message、close_session
* */
export interface Session {
    webio_session_id: string;

    // add session creation callback
    on_session_create(callback: () => void): void;

    // add session close callback
    on_session_close(callback: () => void): void;

    // add session message received callback
    on_server_message(callback: (msg: Command) => void): void;

    start_session(debug: boolean): void;

    // send text message to server
    send_message(msg: ClientEvent, onprogress?: (loaded: number, total: number) => void): void;

    // send binary message to server
    send_buffer(data: Blob, onprogress?: (loaded: number, total: number) => void): void;

    close_session(): void;

    closed(): boolean;
}

function safe_poprun_callbacks(callbacks: (() => void)[], name = 'callback') {
    while (callbacks.length)
        try {
            callbacks.pop().call(this);
        } catch (e) {
            console.log('Error in %s: %s', name, e);
        }
}

export class SubPageSession implements Session {
    webio_session_id: string = '';
    debug: boolean;
    private _master_id: string;
    private _master_window: any;
    private _closed: boolean = false;

    private _session_create_callbacks: (() => void)[] = [];
    private _session_close_callbacks: (() => void)[] = [];
    private _on_server_message: (msg: Command) => any = () => {
    };

    // check if the window is a pywebio subpage
    static is_sub_page(window_obj: Window = window): boolean {
        try {
            // @ts-ignore
            if (window_obj._pywebio_page_args !== undefined) {
                // @ts-ignore
                if (window_obj.opener !== null && window_obj.opener.WebIO !== undefined)
                    return true;

                // @ts-ignore
                if (window_obj.parent != window_obj && window_obj.parent.WebIO !== undefined)
                    return true;
            }
        } catch (e) {
        }
        return false;
    }

    // check if the master page is active
    is_master_active(): boolean {
        return this._master_window && this._master_window.WebIO &&
            !this._master_window.WebIO._state.CurrentSession.closed() &&
            this._master_id == this._master_window.WebIO._state.Random;
    }

    on_session_create(callback: () => any): void {
        this._session_create_callbacks.push(callback);
    };

    on_session_close(callback: () => any): void {
        this._session_close_callbacks.push(callback);
    }

    on_server_message(callback: (msg: Command) => any): void {
        this._on_server_message = callback;
    }

    start_session(debug: boolean): void {
        this.debug = debug;
        safe_poprun_callbacks(this._session_create_callbacks, 'session_create_callback');

        // @ts-ignore
        let page_args:PageArgs = window._pywebio_page_args;

        this._master_window = page_args.master_window;
        this._master_id = this._master_window.WebIO._state.Random;

        page_args.page_session.resolve(this);

        let check_active_id = setInterval(() => {
            if (!this.is_master_active())
                this.close_session();
            if (this.closed())
                clearInterval(check_active_id);
        }, 300);

        if (window.parent != window) { // this window is in an iframe
            // show page close button
            let close_btn = $('<button title="Close Page" type="button" class="pywebio-page-close-btn btn-close"></button>').on('click', () => {
                page_args.on_terminate()
            });
            $('body').append(close_btn);
        }
    };

    // called by master, transfer command to this session
    server_message(command: Command) {
        if (this.debug)
            console.info('>>>', command);
        this._on_server_message(command);
    }

    // send text message to master
    send_message(msg: ClientEvent, onprogress?: (loaded: number, total: number) => void): void {
        if (this.closed() || !this.is_master_active())
            return error_alert(t("disconnected_with_server"));
        this._master_window.WebIO._state.CurrentSession.send_message(msg, onprogress);
    }

    // send binary message to master
    send_buffer(data: Blob, onprogress?: (loaded: number, total: number) => void): void {
        if (this.closed() || !this.is_master_active())
            return error_alert(t("disconnected_with_server"));
        this._master_window.WebIO._state.CurrentSession.send_buffer(data, onprogress);
    }

    close_session(): void {
        this._closed = true;
        safe_poprun_callbacks(this._session_close_callbacks, 'session_close_callback');
    }

    closed(): boolean {
        return this._closed;
    }
}

export class WebSocketSession implements Session {
    ws: WebSocket;
    debug: boolean;
    webio_session_id: string = 'NEW';
    private _closed: boolean; // session logical closed (by `close_session` command)
    private _session_create_ts = 0;
    private _session_create_callbacks: (() => void)[] = [];
    private _session_close_callbacks: (() => void)[] = [];
    private _on_server_message: (msg: Command) => any = () => {
    };

    constructor(public ws_api: string, public app_name: string = 'index') {
        this.ws = null;
        this.debug = false;
        this._closed = false;
    }

    set_ws_api() {
        let url = new URL(this.ws_api);
        if (url.protocol !== 'wss:' && url.protocol !== 'ws:') {
            let protocol = url.protocol || window.location.protocol;
            url.protocol = protocol.replace('https', 'wss').replace('http', 'ws');
        }
        url.search = `?app=${this.app_name}&session=${this.webio_session_id}`;
        this.ws_api = url.href;
    }

    on_session_create(callback: () => any): void {
        this._session_create_callbacks.push(callback);
    };

    on_session_close(callback: () => any): void {
        this._session_close_callbacks.push(callback);
    }

    on_server_message(callback: (msg: Command) => any): void {
        this._on_server_message = callback;
    }

    start_session(debug: boolean = false): void {
        let that = this;

        this.set_ws_api();

        this._session_create_ts = Date.now();
        this.debug = debug;
        this.ws = new WebSocket(this.ws_api);
        this.ws.onopen = () => {
            safe_poprun_callbacks(this._session_create_callbacks, 'session_create_callback');
        };

        this.ws.onclose = function (evt) {
            if (!that._closed && that.webio_session_id != 'NEW') {  // not receive `close_session` command && enabled reconnection
                const session_create_interval = 5000;
                if (Date.now() - that._session_create_ts > session_create_interval)
                    that.start_session(that.debug);
                else
                    setTimeout(() => {
                        that.start_session(that.debug);
                    }, session_create_interval - Date.now() + that._session_create_ts);
            } else {
                that.close_session();
            }
        };
        this.ws.onmessage = function (evt) {
            let msg: Command = JSON.parse(evt.data);
            if (debug) console.info('>>>', JSON.parse(evt.data));
            that._on_server_message(msg);
        };
    }

    start_onprogress(onprogress?: (loaded: number, total: number) => void): void {
        let total = this.ws.bufferedAmount;
        let onprogressID = setInterval(() => {
            let loaded = total - this.ws.bufferedAmount;
            onprogress(loaded, total);
            if (this.ws.bufferedAmount == 0)
                clearInterval(onprogressID);
        }, 200);
    }

    send_message(msg: ClientEvent, onprogress?: (loaded: number, total: number) => void): void {
        if (this.closed())
            return error_alert(t("disconnected_with_server"));

        if (this.ws === null)
            return console.error('WebSocketWebIOSession.ws is null when invoke WebSocketWebIOSession.send_message. ' +
                'Please call WebSocketWebIOSession.start_session first');
        this.ws.send(JSON.stringify(msg));

        if (onprogress)
            this.start_onprogress(onprogress);

        if (this.debug) console.info('<<<', msg);
    }

    send_buffer(data: Blob, onprogress?: (loaded: number, total: number) => void): void {
        if (this.closed())
            return error_alert(t("disconnected_with_server"));

        if (this.ws === null)
            return console.error('WebSocketWebIOSession.ws is null when invoke WebSocketWebIOSession.send_message. ' +
                'Please call WebSocketWebIOSession.start_session first');

        this.ws.send(data);

        if (onprogress)
            this.start_onprogress(onprogress);

        if (this.debug) console.info('<<< Blob data...');
    }

    close_session(): void {
        this._closed = true;
        safe_poprun_callbacks(this._session_close_callbacks, 'session_close_callback');
        CloseSession()
        try {
            this.ws.close();
        } catch (e) {
        }
    }

    closed(): boolean {
        return this._closed || this.ws.readyState === WebSocket.CLOSED || this.ws.readyState === WebSocket.CLOSING;
    }
}


export class HttpSession implements Session {
    interval_pull_id: number = null;
    webio_session_id: string = 'NEW';
    debug = false;

    private _closed = false;
    private _session_create_callbacks: (() => void)[] = [];
    private _session_close_callbacks: (() => void)[] = [];
    private _on_server_message: (msg: Command) => void = () => {
    };


    constructor(public api_url: string, app_name = 'index', public pull_interval_ms = 1000) {
        let url = new URL(api_url, window.location.href);
        url.search = "?app=" + app_name;
        this.api_url = url.href;
    }

    on_session_create(callback: () => void): void {
        this._session_create_callbacks.push(callback);
    }

    on_session_close(callback: () => void): void {
        this._session_close_callbacks.push(callback);
    }

    on_server_message(callback: (msg: Command) => void): void {
        this._on_server_message = callback;
    }

    start_session(debug: boolean = false): void {
        this.debug = debug;
        this.pull();
        this.interval_pull_id = setInterval(() => {
            this.pull()
        }, this.pull_interval_ms);
    }

    pull() {
        let that = this;
        $.ajax({
            type: "GET",
            url: this.api_url,
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            headers: {"webio-session-id": this.webio_session_id},
            success: function (data: Command[], textStatus: string, jqXHR: JQuery.jqXHR) {
                safe_poprun_callbacks(that._session_create_callbacks, 'session_create_callback');
                that._on_request_success(data, textStatus, jqXHR);
            },
            error: function () {
                console.error('Http pulling failed');
            }
        })
    }

    private _on_request_success(data: Command[], textStatus: string, jqXHR: JQuery.jqXHR) {
        let sid = jqXHR.getResponseHeader('webio-session-id');
        if (sid) this.webio_session_id = sid;

        for (let msg of data) {
            if (this.debug) console.info('>>>', msg);
            this._on_server_message(msg);
        }
    };

    send_message(msg: ClientEvent, onprogress?: (loaded: number, total: number) => void): void {
        if (this.debug) console.info('<<<', msg);
        this._send({
            data: JSON.stringify(msg),
            contentType: "application/json; charset=utf-8",
        }, onprogress);
    }

    send_buffer(data: Blob, onprogress?: (loaded: number, total: number) => void): void {
        if (this.debug) console.info('<<< Blob data...');
        this._send({
            data: data,
            cache: false,
            processData: false,
            contentType: 'application/octet-stream',
        }, onprogress);
    }

    _send(options: { [key: string]: any; }, onprogress?: (loaded: number, total: number) => void): void {
        if (this.closed())
            return error_alert(t("disconnected_with_server"));

        $.ajax({
            ...options,
            type: "POST",
            url: this.api_url,
            dataType: "json",
            headers: {"webio-session-id": this.webio_session_id},
            success: this._on_request_success.bind(this),
            xhr: function () {
                let xhr = new window.XMLHttpRequest();
                // Upload progress
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable && onprogress) {
                        onprogress(evt.loaded, evt.total);
                    }
                }, false);
                return xhr;
            },
            error: function () {
                console.error('Http push blob data failed');
                error_alert(t("connect_fail"));
            }
        });
    }

    close_session(): void {
        this._closed = true;
        safe_poprun_callbacks(this._session_close_callbacks, 'session_close_callback');
        CloseSession()
        clearInterval(this.interval_pull_id);
    }

    closed(): boolean {
        return this._closed;
    }

    change_pull_interval(new_interval: number): void {
        clearInterval(this.interval_pull_id);
        this.pull_interval_ms = new_interval;
        this.interval_pull_id = setInterval(() => {
            this.pull()
        }, this.pull_interval_ms);
    }
}

/*
* Check backend type: http or ws
* Usage:
*   detect_backend('http://localhost:8080/io').then(function(backend_type){ });
* */
export function detect_backend(backend_addr: string) {
    let url = new URL(backend_addr);
    let protocol = url.protocol || window.location.protocol;
    url.protocol = protocol.replace('wss', 'https').replace('ws', 'http');
    backend_addr = url.href;

    return new Promise(function (resolve, reject) {
        $.get(backend_addr, {test: 1}, undefined, 'html').done(function (data: string) {
            resolve(data === 'ok' ? 'http' : 'ws');
        }).fail(function (e: JQuery.jqXHR) {
            resolve('ws');
        });
    });
}


// Send data to backend
export function pushData(data: any, callback_id: string) {
    if (state.CurrentSession === null)
        return console.error("can't invoke PushData when WebIOController is not instantiated");

    state.CurrentSession.send_message({
        event: "callback",
        task_id: callback_id,
        data: data
    });
}