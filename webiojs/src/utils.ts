// Indexable Types

interface Dict {
    [index: string]: any;
}

export class LRUMap {
    keys: string[] = [];
    map: Dict = {};

    push(key: string, value: any) {
        if (key in this.map)
            return console.error("LRUMap: key:%s already in map", key);
        this.keys.push(key);
        this.map[key] = value;
    };

    get_value(key: string) {
        return this.map[key];
    };

    get_top() {
        let top_key = this.keys[this.keys.length - 1];
        return this.map[top_key];
    };

    set_value(key: string, value: any) {
        if (!(key in this.map))
            return console.error("LRUMap: key:%s not in map when call `set_value`", key);
        this.map[key] = value;
    };

    move_to_top(key: string) {
        const index = this.keys.indexOf(key);
        if (index > -1) {
            this.keys.splice(index, 1);
            this.keys.push(key);
        } else {
            return console.error("LRUMap: key:%s not in map when call `move_to_top`", key);
        }
    };

    remove(key: string) {
        if (key in this.map) {
            delete this.map[key];
            this.keys.splice(this.keys.indexOf(key), 1);
        } else {
            return console.error("LRUMap: key:%s not in map when call `remove`", key);
        }
    };

}


export function b64toBlob(b64Data: string, contentType = 'application/octet-stream', sliceSize = 512) {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);

        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, {type: contentType});
    return blob;
}

export function make_set(arr: string[]) {
    let set: { [i: string]: string } = {};
    for (let val of arr)
        set[val] = '';
    return set;
}

export function deep_copy(obj: any): any {
    return JSON.parse(JSON.stringify(obj));
}


// container 为带有滚动条的元素
export function body_scroll_to(target: JQuery, position = 'top', complete?: (this: HTMLElement) => void, offset = 0) {
    let scrollTop = null;
    if (position === 'top')
        scrollTop = target.offset().top;
    else if (position === 'middle')
        scrollTop = target.offset().top + 0.5 * target[0].clientHeight - 0.5 * $(window).height();
    else if (position === 'bottom')
        scrollTop = target[0].clientHeight + target.offset().top - $(window).height();

    let container = $('body,html');
    let speed = Math.abs(container.scrollTop() - scrollTop - offset);
    if (scrollTop !== null)
        container.stop().animate({scrollTop: scrollTop + offset}, Math.min(speed, 500) + 100, complete);
}

// container 为带有滚动条的元素
export function box_scroll_to(target: JQuery, container: JQuery, position = 'top', complete?: (this: HTMLElement) => void, offset = 0) {
    let scrollTopOffset = null;
    if (position === 'top')
        scrollTopOffset = target[0].getBoundingClientRect().top - container[0].getBoundingClientRect().top;
    else if (position === 'middle')
        scrollTopOffset = target[0].getBoundingClientRect().top - container[0].getBoundingClientRect().top - container.height() * 0.5 + target.height() * 0.5;
    else if (position === 'bottom')
        scrollTopOffset = target[0].getBoundingClientRect().bottom - container[0].getBoundingClientRect().bottom;

    let speed = Math.min(Math.abs(scrollTopOffset + offset), 500) + 100;
    if (scrollTopOffset !== null)
        container.stop().animate({scrollTop: container.scrollTop() + scrollTopOffset + offset}, speed, complete);
}


export function randomid(length: number) {
    let result = '';
    let characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let charactersLength = characters.length;
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
}

// 跳转PyWebIO Application
// name: app名称
// new_window: 是否在新窗口打开
export function openApp(name: string, new_window: boolean) {
    let url = new URL(window.location.href);
    url.searchParams.set("app", name);
    if (new_window)
        window.open(url.href);
    else
        window.location.href = url.href;
}


export function error_alert(text: string, duration: number = 1.5) {
    Toastify({
        text: Mustache.escape(text),
        duration: duration * 1000,
        gravity: "top",
        position: 'center',
        backgroundColor: '#e53935',
    }).showToast();
}


// make File object to Blob
export function serialize_file(file: File, input_name: string) {
    let header = {
        'filename': file.name,
        'size': file.size,
        'mime_type': file.type,
        'last_modified': file.lastModified / 1000,
        'input_name': input_name
    }
    return new Blob([serialize_json(header), int2bytes(file.size), file], {type: 'application/octet-stream'});
}

// make json object to Blob
export function serialize_json(json_obj: any) {
    let json_str = JSON.stringify(json_obj);
    const encoder = new TextEncoder();
    const json_buf = encoder.encode(json_str).buffer;
    return new Blob([int2bytes(json_buf.byteLength), json_buf], {type: 'application/octet-stream'});
}

function int2bytes(num: number) {
    const buf = new ArrayBuffer(8);
    const dataView = new DataView(buf);
    dataView.setUint32(0, (num / 4294967296) | 0); // 4294967296 == 2^32
    dataView.setUint32(4, num | 0);
    return buf;
}