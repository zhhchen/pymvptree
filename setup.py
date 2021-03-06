#!/usr/bin/env python
from setuptools import setup, find_packages
import os
from distutils import sysconfig

# # Disable optimizations.
# cflags = sysconfig.get_config_vars()['CFLAGS']
# 
# sysconfig.get_config_vars()['CFLAGS'] = ' '.join(
#     flag for flag in cflags.split() if flag != '-O3')

HERE = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(HERE, 'README.rst'), encoding='utf-8').read()

VERSION = '2.0.0'

setup(name='pymvptree',
      version=VERSION,
      description="Python mvptree wrapper.",
      long_description=README + '\n\n',
      setup_requires=['cffi==1.3.1'],
      cffi_modules=['pymvptree/build_mvptree.py:ffi'],
      install_requires=['cffi==1.3.1'],
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python :: 3.5',
      ],
      keywords='mvptree',
      author='Roberto Abdelkader Mart\xc3\xadnez P\xc3\xa9rez',
      author_email='robertomartinezp@gmail.com',
      url='https://github.com/nilp0inter/pymvptree',
      license='GPLv3',
      packages=find_packages(exclude=["tests", "docs"]),
      include_package_data=True,
      zip_safe=False,)
