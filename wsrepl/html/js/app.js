
var input_item = {
    html:'',
    set_invalid: msg => {},
    set_valid: msg => {},

};


function InputItem(ele, name) {
    this.ele = ele;
    this.name = name;
    this.set_invalid;
    this.set_valid;

    this.set_attr; // 设置input的tag属性


}


function get_handles(ws) {
    var md_parser = new Mditor.Parser();
    var output_container = $('#markdown-body');
    var input_container = $('#input-container');


    var handles = {
        text_input: function (spec) {

            var html = `<h5 class="card-header">需要您输入</h5>
            <div class="card-body">
            <form action="" id="input-form">
                <label for="input-1">name</label>
                <div class="input-group mb-3">
                    <input type="text" class="form-control" placeholder="${spec.prompt}"
                           aria-label="${spec.prompt}" id="input-1" autocomplete="off">
                    <div class="input-group-append">
                        <button class="btn btn-outline-secondary" type="submit" id="button-submit" >提交</button>
                    </div>
                </div>
            </form>
            </div>`;
            input_container.empty();
            input_container.html(html);
            input_container.show(100);

            $('#input-1').focus();

            // console.log(spec, html, input_container.html());

            $('#input-form').submit(function (e) {
                e.preventDefault(); // avoid to execute the actual submit of the form.

                ws.send(JSON.stringify({msg_id: spec.msg_id, data: $('#input-1').val()}));

                input_container.hide(100);
                input_container.empty();

                // setTimeout(function () {
                //
                // }, 200);
            });


        },
        text_print: function (spec) {
            output_container[0].innerHTML += md_parser.parse(spec.content);
        }

    };

    return handles;
}

