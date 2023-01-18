# -*- coding: utf8 -*-
from distutils.core import setup

# Required packages are included in this list
required_packages = ["clean-text==0.6.0"]

setup(
    name="midterm",
    version="0.1",
    description="Lib to facilitate the MEIU22 project",
    author="OSoMe",
    packages=["midterm"],
    install_requires=required_packages,
)
