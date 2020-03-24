from setuptools import setup, find_packages
from pywebio import version

setup(
    name='PyWebIO',
    version=version,
    description=u'Make your python interactive script be a web service.',
    url='https://github.com/wang0618/pywebio',
    author='WangWeimin',
    author_email='wang0.618@qq.com',
    license='MIT',
    packages=find_packages(),
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        "pywebio": [
            "html/codemirror/material-ocean.css",
            "html/codemirror/darcula.css",
            "html/codemirror/active-line.js",
            "html/codemirror/matchbrackets.js",
            "html/codemirror/loadmode.js",
            "html/codemirror/nginx.js",
            "html/codemirror/python.js",
            "html/index.html",
            "html/css/mditor.min.css",
            "html/css/mditor.min.css.map",
            "html/css/codemirror.css",
            "html/css/mditor.css.map",
            "html/css/mditor.css",
            "html/css/app.css",
            "html/js/FileSaver.min.js",
            "html/js/mditor.min.js",
            "html/js/codemirror.js",
            "html/js/mustache.min.js",
            "html/js/form.js",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[
        'tornado>=4.3.0',  # After this version, the new async/await keywords in Python 3.5 are supported
    ],
    extras_require={
        'flask': ['flask'],
    },
)
