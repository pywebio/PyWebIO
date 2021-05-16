export class InputItem {
    static accept_input_types: string[] = [];


    on_input_event: (event_name: string, input_item: InputItem) => void;
    spec: any;
    task_id: string;

    element: JQuery = null; // 在 create_element() 时赋值

    constructor(spec: any, task_id: string, on_input_event: (event_name: string, input_item: InputItem) => void) {
        this.spec = spec;
        this.task_id = task_id;
        this.on_input_event = on_input_event;
    }

    create_element(): JQuery {
        throw new Error("Not implement!");
    }

    update_input(spec: any): any {
        throw new Error("Not implement!");
    }

    // return a value or promise
    get_value(): any {
        throw new Error("Not implement!");
    }

    // 检查输入项的有效性，在表单提交时调用
    check_valid(): boolean {
        return true;
    }

    //在表单加入DOM树后触发
    after_add_to_dom(): any {

    }

    //在表单被显示后触发
    after_show(first_show: boolean): any {

    }

    /*
    * input_idx: 更新作用对象input标签的索引, -1 为不指定对象
    * attributes：更新值字典
    * */
    protected update_input_helper(input_idx: number, attributes: { [i: string]: any }) {
        let attr2selector: { [i: string]: string } = {
            'invalid_feedback': 'div.invalid-feedback',
            'valid_feedback': 'div.valid-feedback',
            'help_text': 'small.text-muted',
            'label': '>label',
        };
        for (let attribute in attr2selector) {
            if (attribute in attributes) {
                this.element.find(attr2selector[attribute]).text(attributes[attribute]);
                delete attributes[attribute];
            }
        }
        let input_elem = this.element.find('input,select,textarea');
        if (input_idx >= 0)
            input_elem = input_elem.eq(input_idx);

        if ('valid_status' in attributes) {
            let class_name = attributes.valid_status ? 'is-valid' : 'is-invalid';
            if (attributes.valid_status === 0) class_name = '';  // valid_status为0时，表示清空valid_status标志
            input_elem.removeClass('is-valid is-invalid').addClass(class_name);
            delete attributes.valid_status;
        }
        input_elem.prop(attributes);
    }
}



