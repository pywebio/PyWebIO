import {Session} from "./session";

// 运行时状态
export let state = {
    AutoScrollBottom: false,  // 是否有新内容时自动滚动到底部
    CurrentSession: null as Session,  // 当前正在活跃的会话
    ShowDuration: 200,  // ms, 显示表单的过渡动画时长
    InputPanelMinHeight: 300,  // 输入panel的最小高度
    InputPanelInitHeight: 300,  // 输入panel的初始高度
    FixedInputPanel:true,
    AutoFocusOnInput:true
};

// 应用配置
export let config = {
    codeMirrorModeURL: "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/mode/%N/%N.min.js",
    codeMirrorThemeURL: "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.52.2/theme/%N.min.css",
    outputAnimation: true, // 启用内容输出动画
    httpPullInterval: 1000,  // HttpSession 拉取消息的周期（ms）
    debug: false,  // 调试模式， 打印所有交互的消息
};
