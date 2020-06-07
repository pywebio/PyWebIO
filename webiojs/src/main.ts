import {config as appConfig, state} from "./state";
import {Command, HttpSession, is_http_backend, Session, WebSocketSession} from "./session";
import {InputHandler} from "./handlers/input"
import {OutputHandler} from "./handlers/output"
import {DisplayAreaButtonOnClick} from "./models/output"
import {CloseHandler, CommandDispatcher} from "./handlers/base"
import {PopupHandler} from "./handlers/popup";

// 获取后端API地址
function get_backend_addr() {
    const url = new URLSearchParams(window.location.search);
    let uri = url.get('pywebio_api') || './io';
    return new URL(uri, window.location.href).href;
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

    let dispatcher = new CommandDispatcher(output_ctrl, input_ctrl, popup_ctrl, close_ctrl);

    webio_session.on_server_message((msg: Command) => {
        let ok = dispatcher.dispatch_message(msg);
        if (!ok)
            console.error('Unknown command:%s', msg.command);
    });
}

function startWebIOClient(output_container_elem: JQuery, input_container_elem: JQuery, app_name: string, config: { [name: string]: any }) {
    for (let key in config) {
        // @ts-ignore
        appConfig[key] = config[key];
    }
    const backend_addr = get_backend_addr();
    is_http_backend(backend_addr).then(function (http_backend) {
        let session;
        if (http_backend)
            session = new HttpSession(backend_addr, app_name, appConfig.httpPullInterval);
        else
            session = new WebSocketSession(backend_addr, app_name);
        set_up_session(session, output_container_elem, input_container_elem);
        session.start_session(appConfig.debug);
    });

}

// @ts-ignore
window.WebIO = {
    'startWebIOClient': startWebIOClient,
    'DisplayAreaButtonOnClick': DisplayAreaButtonOnClick,
};