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
