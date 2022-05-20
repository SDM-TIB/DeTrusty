#!/usr/bin/env python3
import setuptools

with open("VERSION", "r", encoding="utf-8") as ver:
    version = ver.read()

setuptools.setup(
    name='DeTrusty',
    version=version,
    description='DeTrusty - Decentralized and Trustable Query Engine',
    author='Philipp D. Rohde',
    author_email='philipp.rohde@tib.eu',
    scripts=['./Scripts/create_rdfmts.py',
             './Scripts/restart_workers.sh'],
    package_dir={"": "DeTrusty"},
    packages=setuptools.find_packages(where="DeTrusty"),
    install_requires=['requests==2.27.1',
                      'Flask==2.0.3',
                      'ply==3.11'],
    include_package_data=True,
    license='GNU/GPL v3',
    python_requires='>=3.8',
    zip_safe=False
)
