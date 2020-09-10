#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages

setup(name='DeTrusty',
      version='0.1.0',
      description='DeTrusty - Decentralized and Trustable Query Engine',
      author='Philipp D. Rohde',
      author_email='philipp.rohde@tib.eu',
      scripts=[],
      packages=find_packages(),
      install_requires=['requests==2.24.0',
                        'Flask==1.1.2'],
      include_package_data=True,
      license='GNU/GPL v3')
