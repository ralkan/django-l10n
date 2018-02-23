#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

VERSION = (0, 0, 4)
__version__ = '.'.join(map(str, VERSION))

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

packages = find_packages()

setup(
    name='django-l10n',
    version=__version__,
    description='A different approach to Django localization',
    long_description=README,
    url='https://github.com/ralkan/django-l10n',
    download_url='https://github.com/ralkan/django-l10n/tarball/%s' % (
        __version__,),
    author='Resul Alkan',
    author_email='me@resulalkan.com',
    license='MIT',
    keywords='django,l10n,i18n,django language,django localization',
    packages=packages,
    install_requires=[
        'Django==1.7.10',
        'toml==0.9.4'
    ]
)
