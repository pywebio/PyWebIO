from setuptools import setup, find_packages

setup(
    name='webio',
    version='1.0.0',
    description='Spider utils lib',
    url='',
    author='WangWeimin',
    author_email='wangweimin@buaa.edu.com',
    license='MIT',
    packages=find_packages(),
    package_data={
        # data files need to be listed both here (which determines what gets
        # installed) and in MANIFEST.in (which determines what gets included
        # in the sdist tarball)
        "wsrepl": [
            "html",
            "html/codemirror",
            "html/codemirror/material-ocean.css",
            "html/codemirror/darcula.css",
            "html/codemirror/active-line.js",
            "html/codemirror/matchbrackets.js",
            "html/codemirror/loadmode.js",
            "html/codemirror/nginx.js",
            "html/codemirror/python.js",
            "html/index.html",
            "html/.DS_Store",
            "html/css",
            "html/css/mditor.min.css",
            "html/css/mditor.min.css.map",
            "html/css/codemirror.css",
            "html/css/mditor.css.map",
            "html/css/mditor.css",
            "html/js",
            "html/js/FileSaver.min.js",
            "html/js/mditor.min.js",
            "html/js/.DS_Store",
            "html/js/codemirror.js",
            "html/js/async.min.js",
            "html/js/mustache.min.js",
            "html/js/form.js",
            "html/js/app.js",
            "html/bs.html",
            "html/font",
            "html/font/a48ac41620cd818c5020d0f4302489ff.ttf",
            "html/font/af7ae505a9eed503f8b8e6982036873e.woff2",
            "html/font/674f50d287a8c48dc19ba404d20fe713.eot",
            "html/font/b06871f281fee6b241d60582ae9369b9.ttf",
            "html/font/912ec66d7572ff821749319396470bde.svg",
            "html/font/fee66e712a8a08eef5805a46892932ad.woff",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[
        'tornado>=4.2.0',
    ]
)
