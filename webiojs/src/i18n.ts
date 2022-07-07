// @ts-ignore
const userLangCode: string = (navigator.language || navigator.userLanguage || 'en').toLowerCase();

const langPrefix: string = userLangCode.split('-')[0];

export let customMessage: { [msgid: string]: string } = {};

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
        "duplicated_pin_name": "This pin widget has expired (due to the output of a new pin widget with the same name).",
        "browse_file": "Browse",
        "duplicated_scope_name": "Error: The name of this scope is duplicated with the previous one!",
        "page_blocked": "Failed to open new page: blocked by browser",
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
        "browse_file": "浏览文件",
        "duplicated_scope_name": "错误: 此scope与已有scope重复!",
        "page_blocked": "无法打开新页面(页面被浏览器拦截)",
    },
    "ru": {
        "disconnected_with_server": "Соединение с сервером потеряно, пожалуйста перезагрузите страницу",
        "connect_fail": "Ошибка подключения к серверу!",
        "error_in_input": "Пожалуйста, сначала исправьте ошибку",
        "file_size_exceed": 'Файл "%1" весит слишком много: максимально допустимый размер файла - %2',
        "file_total_size_exceed": "Общий размер файлов превышен: максимально допустимый объем - %1",
        "submit": "Отправить",
        "reset": "Сброс",
        "cancel": "Отмена",
        "duplicated_pin_name": "Этот закреп виджет устарел (виджет с таким же именем был выведен).",
        "browse_file": "Обзор",
    },
    "de": {
        "disconnected_with_server": "Verbindung zum Server unterbrochen. Bitte laden Sie die Seite neu.",
        "connect_fail": "Verbindung zum Server nicht möglich!",
        "error_in_input": "Die Eingabe ist fehlerhaft. Bitte beheben Sie zuerst den Fehler.",
        "file_size_exceed": 'Die Größe der Datei "%1" überschreitet das zulässige Maximum: eine einzelne Datei darf nicht größer sein als %2.',
        "file_total_size_exceed": "Die Gesamtdateigröße überschreitet das zulässige Maximum: alle Dateien zusammen dürfen nicht größer sein als %1.",
        "submit": "Übermitteln",
        "reset": "Zurücksetzen",
        "cancel": "Abbrechen",
        "duplicated_pin_name": "Dieses Pin-Widget ist nicht mehr gültig (Grund: Der Output enthält ein neues Pin-Widget mit dem gleichen Namen).",
        "browse_file": "Durchsuchen",
        "duplicated_scope_name": "Fehler: Der Name dieses Scopes ist mit dem vorhergehenden identisch!",
    },
    "fa": {
        "disconnected_with_server": "اتصال به سرور قطع شده است، لطفا صفحه را رفرش کنید",
        "connect_fail": "ناموفق در اتصال به سرور!",
        "error_in_input": "یک خطا با ورودی وجود دارد، لطفا ابتدا خطا را برطرف کنید",
        "file_size_exceed": 'اندازه فایل "%1" از حد مجاز بیشتر است: اندازه یک فایل تکی نباید از %2 بیشتر باشد',
        "file_total_size_exceed": "اندازه کلی فایل از حد مجاز بیشتر است: اندازه کلی فایل نباید از %1 بیشتر باشد",
        "submit": "ارسال",
        "reset": "بازنشانی",
        "cancel": "لغو",
        "duplicated_pin_name": "این Pin Widget منقضی شده است (به دلیل خروجی یک Pin Widget جدید با نام یکسان)",
        "browse_file": "مرور",
        "duplicated_scope_name": "خطا: نام این Scope با نام قبلی تکراری است!",
    },
};

translations['custom'] = customMessage // use to customize the message text.

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

export function t(msgid: string, ...args: string[]): string {
    let fmt = null;
    for (let lang of ['custom', userLangCode, langPrefix, 'en']) {
        if (translations[lang] && translations[lang][msgid]) {
            fmt = translations[lang][msgid];
            break;
        }
    }
    if (fmt === null)
        throw Error(`No translation for "${msgid}" in "${userLangCode}"`);

    return strfmt.apply(null, [fmt, ...args]);
}
