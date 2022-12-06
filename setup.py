#!/usr/bin/env python3
import setuptools

with open("VERSION", "r", encoding="utf-8") as ver:
    version = ver.read()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='DeTrusty',
    version=version,
    description='DeTrusty - Decentralized and Trustable Query Engine',
    license='GNU/GPLv3',
    author='Philipp D. Rohde',
    author_email='philipp.rohde@tib.eu',
    url='https://github.com/SDM-TIB/DeTrusty',
    download_url='https://github.com/SDM-TIB/DeTrusty/archive/refs/tags/v' + version + '.tar.gz',
    long_description=long_description,
    long_description_content_type="text/markdown",
    scripts=['./Scripts/create_rdfmts.py',
             './Scripts/restart_workers.sh'],
    packages=[
        'DeTrusty',
        'DeTrusty.Decomposer',
        'DeTrusty.Molecule',
        'DeTrusty.Operators',
        'DeTrusty.Operators.AnapsidOperators',
        'DeTrusty.Operators.BlockingOperators',
        'DeTrusty.Operators.NonBlockingOperators',
        'DeTrusty.Sparql',
        'DeTrusty.Sparql.Parser',
        'DeTrusty.Wrapper',
        'DeTrusty.Wrapper.RDFWrapper'
    ],
    install_requires=['requests>=2.27.0',
                      'ply==3.11',
                      'rdflib>=6.0.0'],
    include_package_data=True,
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research'
    ]
)
