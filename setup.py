#!/usr/bin/env python3

from setuptools import setup
from pip.req import parse_requirements

install_reqs = parse_requirements('requirements.txt')

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
    package_data={
        'dibi': ['fonts/*', 'styles.qss'],
    },
    install_requires=[
        'PyQt5',
        'mysqlclient',
        'dibi',
        'sshtunnel'
    ],
    extras_require={
        'myloginpath': ['myloginpath'],
    },
    entry_points={
        'console_scripts': [
            'dibi = dibi.dibi:dibi',
        ],
    },
)
