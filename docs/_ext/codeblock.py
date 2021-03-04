import os

from docutils.parsers.rst import directives
from sphinx.directives.code import CodeBlock
import hashlib


class ExportableCodeBlock(CodeBlock):
    option_spec = {
        'summary': directives.unchanged,
        'name': directives.unchanged,
    }

    names = set()

    @staticmethod
    def md5(str_data):
        t = hashlib.md5()
        t.update(str_data.encode('utf-8'))
        return t.hexdigest()

    def run(self):
        if self.env.app.builder.name == 'gettext':
            return super().run()

        code_save_path = os.environ.get('CODE_EXPORT_PATH')
        caption = self.options.get('summary', '')

        if code_save_path and not os.path.exists(code_save_path):
            os.mkdir(code_save_path)

        code_id = self.md5('\n'.join(self.content))[-5:]
        if self.options.get('name', None) is None:
            # 设置name属性，从而让生成的代码html块具有id属性
            self.options.update({'name': 'demo-' + code_id})
        else:
            name = self.options.get('name', '')
            self.options.update({'name': 'demo-' + name})

        name = self.options.get('name').replace('_', '-')
        if name in type(self).names:
            name += '-' + code_id
            self.options.update({'name': name})
        else:
            type(self).names.add(name)

        # 设置特殊class值，用于在js中搜索
        classes = self.options.get('class', [])
        classes.append('demo-cb')
        self.options.update({'class': classes})

        raw_content_text = '\n'.join(self.content)

        content, self.content = self.content, []
        for c in content:
            if '..demo-only' in c or '## ----' in c:
                continue
            c = c.replace('# ..doc-only', '')
            self.content.append(c)

        nodes = super().run()

        try:
            elem_id = nodes[0]['ids'][0]
        except IndexError:
            elem_id = None

        if code_save_path and elem_id:
            fpath = os.path.join(code_save_path, elem_id)
            open(fpath, 'w').write(caption + '\n\n' + raw_content_text)

        return nodes


def setup(app):
    app.add_directive("exportable-codeblock", ExportableCodeBlock)
    app.add_js_file('pywebio.js')

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
