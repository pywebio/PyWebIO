// @ts-ignore
const userLangCode: string = (navigator.language || navigator.userLanguage || 'en').toLowerCase();

const userLang: string = userLangCode.split('-')[0];


const translations: { [lang: string]: { [msgid: string]: string } } = {
    "en": {
        "disconnected_with_server": "Disconnected from the server, please refresh the page",
        "connect_fail": "Failed to connect to server!",
        "error_in_input": "There is an error with the input, please fix the error first",
        "file_size_exceed": 'File "%1" size exceeds limit: the size of a single file must not exceed %2',
        "file_total_size_exceed": "The total file size exceeds the limit: the total file size must not exceed %1",
        "submit": "Submit",
        "reset": "Reset",
        "cancel": "Cancel",
        "duplicated_pin_name": "This pin widget has expired (due to the output of a new pin widget with the same name ).",
    },
    "zh": {
        "disconnected_with_server": "与服务器连接已断开，请刷新页面重新操作",
        "connect_fail": "连接服务器失败!",
        "error_in_input": "输入项存在错误，请消除错误后再提交",
        "file_size_exceed": '文件"%1"大小超过限制: 单个文件大小不超过%2',
        "file_total_size_exceed": "文件总大小超过限制: 文件总大小不超过%1",
        "submit": "提交",
        "reset": "重置",
        "cancel": "取消",
        "duplicated_pin_name": "该 Pin widget 已失效（由于输出了新的同名 pin widget）",
    },
};


// sprintf equivalent, takes a string and some arguments to make a computed string
// eg: strfmt("%1 dogs are in %2", 7, "the kitchen"); => "7 dogs are in the kitchen"
// eg: strfmt("I like %1, bananas and %1", "apples"); => "I like apples, bananas and apples"
function strfmt(fmt: string) {
    let args = arguments;

    return fmt
    // put space after double % to prevent placeholder replacement of such matches
        .replace(/%%/g, '%% ')
        // replace placeholders
        .replace(/%(\d+)/g, function (str, p1) {
            return args[p1];
        })
        // replace double % and space with single %
        .replace(/%% /g, '%')
}

export function t(msgid: string, ...args:string[]): string {
    let fmt = null;
    for (let lang of [userLangCode, userLang, 'en']) {
        if (translations[lang] && translations[lang][msgid]){
            fmt = translations[lang][msgid];
            break;
        }
    }
    if (fmt === null)
        throw Error(`No translation for "${msgid}" in "${userLangCode}"`);

    return strfmt.apply(null, [fmt, ...args]);
}