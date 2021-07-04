#!/usr/bin/env python3

from distutils.core import setup
from setuptools import find_packages

setup(name='DeTrusty',
      version='0.2.0',
      description='DeTrusty - Decentralized and Trustable Query Engine',
      author='Philipp D. Rohde',
      author_email='philipp.rohde@tib.eu',
      scripts=['./Scripts/create_rdfmts.py',
               './Scripts/restart_workers.sh'],
      packages=find_packages(),
      install_requires=['requests==2.24.0',
                        'Flask==1.1.2',
                        'ply==3.11'],
      include_package_data=True,
      license='GNU/GPL v3',
      python_requires='>=3.8',
      zip_safe=False)
