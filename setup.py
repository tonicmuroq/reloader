# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='reloader',
    version='0.1',
    author='tonic',
    zip_safe=False,
    author_email='tonic@wolege.ca',
    description='A reloader daemon for nginx',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts':[
            'rld=reloader.main:main',
        ],
    },
    install_requires=[
        'jinja2',
    ],
)
