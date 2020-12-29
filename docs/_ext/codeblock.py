import os

from docutils.parsers.rst import directives
from sphinx.directives.code import CodeBlock


class ExportableCodeBlock(CodeBlock):
    option_spec = {
        'summary': directives.unchanged,
        'name': directives.unchanged,
    }

    def run(self):
        code_save_path = os.environ.get('CODE_EXPORT_PATH')
        caption = self.options.get('summary', '')

        if code_save_path and not os.path.exists(code_save_path):
            os.mkdir(code_save_path)

        if self.options.get('name', None) is None:
            # 设置name属性，从而让生成的代码html块具有id属性
            self.options.update({'name': 'demo'})

        classes = self.options.get('class', [])
        classes.append('demo-cb')
        self.options.update({'class': classes})
        content_text = '\n'.join(self.content)

        content, self.content = self.content, []
        for c in content:
            if not c.startswith('## ') and c != '##':
                self.content.append(c)

        nodes = super().run()

        try:
            elem_id = nodes[0]['ids'][0]
        except IndexError:
            elem_id = None

        if code_save_path and elem_id:
            fpath = os.path.join(code_save_path, elem_id)
            open(fpath, 'w').write(caption + '\n\n' + content_text)

        return nodes


def setup(app):
    app.add_directive("exportable-codeblock", ExportableCodeBlock)
    app.add_js_file('pywebio.js')

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
