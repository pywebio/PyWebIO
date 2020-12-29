const DEMO_URL = 'http://pywebio-demos.wangweimin.site/?pywebio_api=doc_demo';

var parseHTML = function (str) {
    let tmp = document.implementation.createHTMLDocument();
    tmp.body.innerHTML = str;
    return tmp.body.children;
};

function ready(fn) {
    if (document.readyState != 'loading') {
        fn();
    } else {
        document.addEventListener('DOMContentLoaded', fn);
    }
}

let demo_url = new URL(DEMO_URL);

ready(function () {
    let codes = document.querySelectorAll('.demo-cb');
    for (let c of codes) {
        let id = c.getAttribute('id');
        let ele = c.querySelector('.highlight > pre');
        demo_url.searchParams.set("app", id);
        let node = parseHTML(`<a class="viewcode-back" href="${demo_url.href}" target="_blank">[Demo]</a>`)[0];
        ele.insertBefore(node, ele.firstChild);
    }
});
