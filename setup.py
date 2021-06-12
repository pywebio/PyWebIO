import os
from functools import reduce

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

about = {}
with open(os.path.join(here, 'pywebio', '__version__.py'), encoding='utf8') as f:
    exec(f.read(), about)

with open('README.md', encoding='utf8') as f:
    readme = f.read()

extras_require = {
    'flask': ['flask>=0.10'],
    'django': ['django>=2.2'],
    'aiohttp': ['aiohttp>=3.1'],
    'bokeh': ['bokeh'],
    'doc': ['sphinx', 'sphinx-tabs'],
}
# 可以使用 pip install pywebio[all] 安装所有额外依赖
extras_require['all'] = reduce(lambda x, y: x + y, extras_require.values())

setup(
    name=about['__package__'],
    version=about['__version__'],
    description=about['__description__'],
    long_description=readme,
    long_description_content_type='text/markdown',
    author=about['__author__'],
    author_email=about['__author_email__'],
    url=about['__url__'],
    license=about['__license__'],
    python_requires=">=3.5.2",
    packages=['pywebio', 'pywebio.session', 'pywebio.platform'],
    scripts=['tools/pywebio-path-deploy'],
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        "pywebio": [
            "html/codemirror/base16-light.min.css",
            "html/codemirror/active-line.js",
            "html/codemirror/matchbrackets.js",
            "html/codemirror/loadmode.js",
            "html/codemirror/python.js",
            "html/css/bootstrap.min.css",
            "html/css/markdown.min.css",
            "html/css/toastify.min.css",
            "html/css/app.css",
            "html/css/codemirror.min.css",
            "html/js/FileSaver.min.js",
            "html/js/prism.min.js",
            "html/js/purify.min.js",
            "html/js/pywebio.min.js",
            "html/js/pywebio.min.js.map",  # only available in dev version
            "html/js/mustache.min.js",
            "html/js/jquery.min.js",
            "html/js/bootstrap.min.js",
            "html/js/bs-custom-file-input.min.js",
            "html/js/popper.min.js",
            "html/js/toastify.min.js",
            "html/js/require.min.js",
            "html/js/codemirror.min.js",
            "html/image/favicon_open_16.png",
            "html/image/favicon_closed_32.png",
            "platform/tpl/index.html"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    install_requires=[
        'tornado>=5.0',
        'user-agents',
    ],
    extras_require=extras_require,
    project_urls={
        'Documentation': 'https://pywebio.readthedocs.io',
        'Source': 'https://github.com/wang0618/PyWebIO',
    },
)
