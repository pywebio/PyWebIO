import {config as appConfig, state} from "./state";
import {ClientEvent, Command, HttpSession, is_http_backend, pushData, Session, WebSocketSession} from "./session";
import {InputHandler} from "./handlers/input"
import {OutputHandler} from "./handlers/output"
import {CloseHandler, CommandDispatcher} from "./handlers/base"
import {PopupHandler} from "./handlers/popup";
import {openApp} from "./utils";
import {ScriptHandler} from "./handlers/script";
import {DownloadHandler} from "./handlers/download";
import {ToastHandler} from "./handlers/toast";
import {EnvSettingHandler} from "./handlers/env";

// 获取后端API的绝对地址
function backend_absaddr(addr: string) {
    return new URL(addr, window.location.href).href;
}

// 初始化Handler和Session
function set_up_session(webio_session: Session, output_container_elem: JQuery, input_container_elem: JQuery) {
    state.CurrentSession = webio_session;
    webio_session.on_session_close(function () {
        $('#favicon32').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAByElEQVRYR82XLUzDUBDH/9emYoouYHAYMGCAYJAYEhxiW2EOSOYwkKBQKBIwuIUPN2g7gSPBIDF8GWbA4DAjG2qitEfesi6lbGxlXd5q393/fr333t07QpdfPp8f0nV9CcACEU0DGAOgN9yrAN6Y+QnATbVavcrlcp/dSFMnI9M0J1RV3WHmFQCJTvaN9RoRXbiuu28YxstfPm0BbNtOMPMeEW0C0LoMHDZzmPmIiHbT6XStlUZLgEKhMK5p2iWAyX8GDruVHMdZzmazr+GFXwCmac4oinINYCSm4L5M2fO8RcMwHoO6PwAaf37bh+BNCMdx5oOZaAKIPQdwF2Pa2yWwBGDOPxNNAMuyDohoK+a0t5Rj5sNMJrMtFusA4qopivLcw2mPyu14njclrmgdoFgsnjLzWlSVXuyJ6CyVSq2TqHDJZPI9QpHpJW7Qt1apVEbJsqwVIjqPSzWKDjOvCoBjItqI4hiXLTOfkG3b9wBm4xKNqPMgAMoAhiM6xmX+IQC+AKhxKUbUcQcCQPoWyD2E0q+h9EIkvRRLb0YD0Y4FhNQHiQCQ/iQTEFIfpX4Nl/os9yGkDiY+hNTRLNhSpQ2n4b7er/H8G7N6BRSbHvW5AAAAAElFTkSuQmCC');
        $('#favicon16').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA0ElEQVQ4T62TPQrCQBCF30tA8BZW9mJtY+MNEtKr2HkWK0Xtw+4NbGysxVorbyEKyZMNRiSgmJ/tZufNNzO7M0ThxHHc8zxvSnIIoPNyXyXt0zRdR1F0+gxhblhr25IWJMcA3vcFviRtSc6DILg5XyZ0wQB2AAbFir7YBwAjB8kAxpg1ycmfwZlM0iYMwyldz77vH3+U/Y2rJEn6NMYsSc7KZM+1kla01p4BdKsAAFwc4A6gVRHwaARQr4Xaj1j7G2sPUiOjnEMqL9PnDJRd5ycpJXsd2f2NIAAAAABJRU5ErkJggg==');
    });

    let output_ctrl = new OutputHandler(webio_session, output_container_elem);
    let input_ctrl = new InputHandler(webio_session, input_container_elem);
    let popup_ctrl = new PopupHandler(webio_session);
    let close_ctrl = new CloseHandler(webio_session);
    let script_ctrl = new ScriptHandler(webio_session);
    let download_ctrl = new DownloadHandler();
    let toast_ctrl = new ToastHandler();
    let env_ctrl = new EnvSettingHandler();

    let dispatcher = new CommandDispatcher(output_ctrl, input_ctrl, popup_ctrl, close_ctrl, script_ctrl, download_ctrl, toast_ctrl, env_ctrl);

    webio_session.on_server_message((msg: Command) => {
        try {
            let ok = dispatcher.dispatch_message(msg);
            if (!ok) console.error('Unknown command:%s', msg.command);
        } catch (e) {
            console.error('Error(%s) in dispatch command: %s', e, msg.command);
        }
    });
}


function startWebIOClient(options: {
    output_container_elem: JQuery,
    input_container_elem: JQuery,
    backend_address: string,
    app_name: string,
    protocol: string, // 'http', 'ws', 'auto'
    runtime_config: { [name: string]: any }
}) {
    for (let key in options.runtime_config) {
        // @ts-ignore
        appConfig[key] = options.runtime_config[key];
    }
    const backend_addr = backend_absaddr(options.backend_address);

    let start_session = (is_http:boolean) => {
        let session;
        if (is_http)
            session = new HttpSession(backend_addr, options.app_name, appConfig.httpPullInterval);
        else
            session = new WebSocketSession(backend_addr, options.app_name);
        set_up_session(session, options.output_container_elem, options.input_container_elem);
        session.start_session(appConfig.debug);
    };
    if(options.protocol=='auto')
        is_http_backend(backend_addr).then(start_session);
    else
        start_session(options.protocol == 'http')
}


// @ts-ignore
window.WebIO = {
    'startWebIOClient': startWebIOClient,
    'sendMessage': (msg: ClientEvent) => {
        return state.CurrentSession.send_message(msg);
    },
    'openApp': openApp,
    'pushData': pushData,
};