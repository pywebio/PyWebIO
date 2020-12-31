## sphinx示例代码添加在线Demo链接

### 自定义sphinx `exportable-codeblock` directive

代码实现：`PyWebIO/docs/_ext/codeblock.py` 

`exportable-codeblock` 指令可以像 `codeblock` 指令一样使用，用于展示代码:

```rest
..exportable-codeblock::
    :name: test
    :summary: 描述
    
    put_text('hello world')
    
```

当设置环境变量 `CODE_EXPORT_PATH` 后进行文档构建时，使用`exportable-codeblock`指令展示的示例代码会被导出到环境变量 `CODE_EXPORT_PATH`指定的目录中。

比如：
```bash
CODE_EXPORT_PATH=/Users/wangweimin/repos/PyWebIO/demos/doc_domes make clean html
```

使用`exportable-codeblock`指令展示的示例代码被导出后，可以使用 `PyWebIO/demos/doc_demo.py` 来运行。

为了在运行示例代码时，可以有更多选项，定义了一些特殊注释，这些特殊不会出现在生成的文档中，但会被导出并在运行示例代码时被特殊处理。

特殊注释如下：

 - `## ----` : 表示分割示例代码，将示例代码分割成不同的部分来分别运行。该注释主要放到行首
 - `# ..demo-only` : 表示该行代码仅在Demo页面中显示 
 - `# ..doc-only` : 表示该行代码仅在文档中显示