import os
from functools import reduce

from setuptools import setup, find_packages

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
    packages=[p for p in find_packages() if p.startswith('pywebio')],
    scripts=['tools/pywebio-path-deploy'],
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        "pywebio": [
            "html/codemirror/*",
            "html/image/*",
            "html/js/*",
            "html/css/*",
            "html/css/bs-theme/*",
            "platform/tpl/index.html"
        ],
    },
    entry_points={
        # pyinstaller hook
        # https://pyinstaller.org/en/stable/hooks.html#providing-pyinstaller-hooks-with-your-package
        'pyinstaller40': [
            'hook-dirs = pywebio.platform.pyinstaller:get_hook_dirs',
        ]
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
