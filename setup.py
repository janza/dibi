#!/usr/bin/env python3

from setuptools import setup

setup(
    name='dibi',
    version='0.1',
    description='Lightweight GUI for MySQL with performance in mind',
    author='Josip Janzic',
    author_email='me@josip.dev',
    url='https://github.com/janza/dibi',
    license='MIT',
    packages=['dibi'],
    include_package_data=True,
    install_requires=[
        'PyQt5',
        'mysqlclient',
        'dibi'
    ],
    entry_points={
        'console_scripts': [
            'dibi = dibi.dibi:dibi',
        ],
    },
)
