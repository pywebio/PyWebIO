import {config as appConfig, state} from "./state";
import {ClientEvent, Command, HttpSession, is_http_backend, pushData, Session, WebSocketSession} from "./session";
import {InputHandler} from "./handlers/input"
import {OutputHandler} from "./handlers/output"
import {SessionCtrlHandler, CommandDispatcher} from "./handlers/base"
import {PopupHandler} from "./handlers/popup";
import {openApp} from "./utils";
import {ScriptHandler} from "./handlers/script";
import {DownloadHandler} from "./handlers/download";
import {ToastHandler} from "./handlers/toast";
import {EnvSettingHandler} from "./handlers/env";
import {PinHandler} from "./handlers/pin";

// 获取后端API的绝对地址
function backend_absaddr(addr: string) {
    return new URL(addr, window.location.href).href;
}

// 初始化Handler和Session
function set_up_session(webio_session: Session, output_container_elem: JQuery, input_container_elem: JQuery) {
    state.CurrentSession = webio_session;
    $('#pywebio-loading').show();
    webio_session.on_session_create(function () {
        $('#pywebio-loading').hide();
        $('#favicon32').attr('href', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAwklEQVQ4T63TvU5CQRCG4WcwMfEuqOgNtQ2Nd4CxV2LHtVhJ0N7AHdjQUBtrrLwLA4ks2Rx+/Qucw3Y78807M7sz4ft5dq6mI7RQX7o/JCNzfdfetkNifRk6k9wLN9jYdxMkyZPQ1faZXYUwB/OCix8V/W4Y4zJDCsBAX7jdM7iQJY+udELu+cTrP2X/xU2+NMPAg3B3UPaVOOmFoQkapQC8Z8AUpyUBs6MAKrZQ+RErf2PlQTrKKK8gpZdpewgOXOcFTTxEjYwMoIkAAAAASUVORK5CYII=');
        $('#favicon16').attr('href', 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABmUlEQVRYR82XK0wDQRCGv21TUUUJGBwGDBggGCSGBIcAWnBAgsNAgkKhSMDgCA8HtEXgSDBIDC9DDRgcpoSiKo52yea49DiutMttsz27M/98N7s7OyNo9tujgxSTwDiCIaAXSH27l4AXJA/AFSUuWOajGWnR0ChLP3HWkWSAZEN716CM4JQKW6R5+sunPkCeJJJNBCtAosnAQTMHyS6CDWYoh2mEAxzTR4JzYOCfgYNuBRymmOc5uPAbIMswMS6BbkPBPZkiVSZIc+/X/Qng/vl1C4LXIBzG/JmoAag9hxuDaa+XwAIw6p2JGkCObQSrhtMeLifZYZY1tegCqKsW4zHCadfldqgyqK6oC3DGIZIFXZVI9oIjplkUqArXyatGkYkU1+dc5p0eQY4MghNTqlo6kjkFsI9gScvRlLHkQJDnFhgxpampc6cAikCXpqMp8zcF8AnETSlq6lTaAsD6Flg+hNavofVCZL0UW3+M2uI5VhBWGxIFYL0lUxBWm1KviFttyz0Iq4OJB2F1NPO/qdaG0+DD3qLx/AuMVJFhmC8dSgAAAABJRU5ErkJggg==');
    });
    webio_session.on_session_close(function () {
        $('#favicon32').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAByElEQVRYR82XLUzDUBDH/9emYoouYHAYMGCAYJAYEhxiW2EOSOYwkKBQKBIwuIUPN2g7gSPBIDF8GWbA4DAjG2qitEfesi6lbGxlXd5q393/fr333t07QpdfPp8f0nV9CcACEU0DGAOgN9yrAN6Y+QnATbVavcrlcp/dSFMnI9M0J1RV3WHmFQCJTvaN9RoRXbiuu28YxstfPm0BbNtOMPMeEW0C0LoMHDZzmPmIiHbT6XStlUZLgEKhMK5p2iWAyX8GDruVHMdZzmazr+GFXwCmac4oinINYCSm4L5M2fO8RcMwHoO6PwAaf37bh+BNCMdx5oOZaAKIPQdwF2Pa2yWwBGDOPxNNAMuyDohoK+a0t5Rj5sNMJrMtFusA4qopivLcw2mPyu14njclrmgdoFgsnjLzWlSVXuyJ6CyVSq2TqHDJZPI9QpHpJW7Qt1apVEbJsqwVIjqPSzWKDjOvCoBjItqI4hiXLTOfkG3b9wBm4xKNqPMgAMoAhiM6xmX+IQC+AKhxKUbUcQcCQPoWyD2E0q+h9EIkvRRLb0YD0Y4FhNQHiQCQ/iQTEFIfpX4Nl/os9yGkDiY+hNTRLNhSpQ2n4b7er/H8G7N6BRSbHvW5AAAAAElFTkSuQmCC');
        $('#favicon16').attr('href', 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAA0ElEQVQ4T62TPQrCQBCF30tA8BZW9mJtY+MNEtKr2HkWK0Xtw+4NbGysxVorbyEKyZMNRiSgmJ/tZufNNzO7M0ThxHHc8zxvSnIIoPNyXyXt0zRdR1F0+gxhblhr25IWJMcA3vcFviRtSc6DILg5XyZ0wQB2AAbFir7YBwAjB8kAxpg1ycmfwZlM0iYMwyldz77vH3+U/Y2rJEn6NMYsSc7KZM+1kla01p4BdKsAAFwc4A6gVRHwaARQr4Xaj1j7G2sPUiOjnEMqL9PnDJRd5ycpJXsd2f2NIAAAAABJRU5ErkJggg==');
    });

    let output_ctrl = new OutputHandler(webio_session, output_container_elem);
    let input_ctrl = new InputHandler(webio_session, input_container_elem);
    let popup_ctrl = new PopupHandler(webio_session);
    let session_ctrl = new SessionCtrlHandler(webio_session);
    let script_ctrl = new ScriptHandler(webio_session);
    let pin_ctrl = new PinHandler(webio_session);
    let download_ctrl = new DownloadHandler();
    let toast_ctrl = new ToastHandler();
    let env_ctrl = new EnvSettingHandler();

    let dispatcher = new CommandDispatcher(output_ctrl, input_ctrl, popup_ctrl, session_ctrl,
        script_ctrl, download_ctrl, toast_ctrl, env_ctrl, pin_ctrl);

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

    let start_session = (is_http: boolean) => {
        let session;
        if (is_http)
            session = new HttpSession(backend_addr, options.app_name, appConfig.httpPullInterval);
        else
            session = new WebSocketSession(backend_addr, options.app_name);
        set_up_session(session, options.output_container_elem, options.input_container_elem);
        session.start_session(appConfig.debug);
    };
    if (options.protocol == 'auto')
        is_http_backend(backend_addr).then(start_session);
    else
        start_session(options.protocol == 'http')
}


// @ts-ignore
window.WebIO = {
    '_state': state,
    'startWebIOClient': startWebIOClient,
    'openApp': openApp,
};