#!/usr/bin/env python

from setuptools import setup

setup(
    setup_requires=['pbr', 'cffi==1.3.1'],
    install_requires=['cffi==1.3.1'],
    cffi_modules=["pymvptree/build_pymvptree.py:ffi"],
    pbr=True,
)
