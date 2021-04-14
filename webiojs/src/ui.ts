import {state} from "./state";

let has_input = false;
let input_panel = $('#input-container');
let input_cards = $('#input-cards');
let end_space = $('#end-space');

export function show_input() {
    close_input();
    has_input = true;
    if (($(window).height() - input_panel[0].getBoundingClientRect().top < input_min_fixed_height() - 40)) {
        toggle_input_panel_style(true);
    }
}

export function close_input() {
    has_input = false;
    if (input_panel.hasClass('fixed')) {
        input_panel.removeClass('fixed');
    }
    input_panel.height('unset');
    end_space.height(0);
}


function input_min_fixed_height() { // 返回当前的输入panel的最小高度
    const min_fixed_height = Math.max(state.InputPanelMinHeight, 75);

    //80 = #input-container.fixed padding-top + padding-bottom
    let now_height = input_cards.height() + 80;

    return Math.min(now_height, min_fixed_height);
}


function fixed_input_init_height() { // 返回当前的输入panel的初始高度
    const init_fixed_height = Math.max(state.InputPanelInitHeight, 175);

    //80 = #input-container.fixed padding-top + padding-bottom
    let now_height = input_cards.height() + 80;

    return Math.min(now_height, init_fixed_height);
}


function toggle_input_panel_style(fixed: boolean) {
    fixed = state.FixedInputPanel && fixed;
    if (!fixed) {
        input_panel.removeClass('fixed');
        end_space.height(0);
        input_panel.height('unset');
    } else {
        let min = fixed_input_init_height();
        end_space.height(min - 40);  // 40 =  #input-container.fixed padding-top
        input_panel.height(min);
        // input_panel显示动画
        // input_panel.height(0);
        // input_panel.stop().animate({height: min}, {duration: 50, easing: 'swing'});
        input_panel.addClass('fixed');
    }
}


function move_input_panel(step: number) {
    let new_height = input_panel.height() + step;
    if (new_height >= input_cards.height())
        new_height = input_cards.height();
    else if (new_height <= input_min_fixed_height() - 80)   //80 = #input-container.fixed padding-top + padding-bottom
        new_height = input_min_fixed_height() - 80;

    input_panel.height(new_height);
    end_space.height(new_height - 40); // 40 =  #input-container.fixed padding-top
}


$(function () {
    input_panel = $('#input-container');
    input_cards = $('#input-cards');
    end_space = $('#end-space');


    let lastScrollTop = 0; // to Detecting scroll direction.  Credits: https://stackoverflow.com/questions/31223341/detecting-scroll-direction
    $(window).on('scroll', function () {
        let st = window.pageYOffset || document.documentElement.scrollTop; // Credits: "https://github.com/qeremy/so/blob/master/so.dom.js#L426"
        let downmove = st < lastScrollTop;
        let upmove = st > lastScrollTop;

        if (!input_panel.hasClass('fixed')) {
            // 40 =  #input-container.fixed padding-top
            if (($(window).height() - input_panel[0].getBoundingClientRect().top < input_min_fixed_height() - 40) && downmove && has_input) {
                toggle_input_panel_style(true);
                st = window.pageYOffset || document.documentElement.scrollTop;
            }
        } else {
            // 到达底部
            // 50 = footer height
            if ($(window).scrollTop() + window.innerHeight > $(document).height() - 50 && upmove) {  // issue $(window).height() < window.innerHeight in mobile phone
                toggle_input_panel_style(false);
                st = window.pageYOffset || document.documentElement.scrollTop;
            }
        }
        lastScrollTop = st <= 0 ? 0 : st; // For Mobile or negative scrolling
    });

    input_panel[0].addEventListener("wheel", function (e) {
        // Credits: https://stackoverflow.com/questions/30892830/detect-scrolling-on-pages-without-a-scroll-bar

        if (!input_panel.hasClass('fixed')) return;
        e.preventDefault();

        // to make it work on IE or Chrome
        // @ts-ignore
        let variation = parseInt(e.deltaY);
        move_input_panel(variation);
    });

    let last_y = -1;
    input_panel[0].addEventListener("touchstart", function (evt) {
        if (evt.changedTouches.length > 1)
            return;
        last_y = evt.changedTouches[0].screenY;
    });


    input_panel[0].addEventListener("touchmove", function (evt) {
        if (!input_panel.hasClass('fixed')) return;
        if (evt.changedTouches.length > 1)
            return;
        evt.preventDefault();
        let variation = last_y - evt.changedTouches[0].screenY;
        last_y = evt.changedTouches[0].screenY;
        move_input_panel(variation);
    });
});
