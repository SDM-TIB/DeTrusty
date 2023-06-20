#####################
DeTrusty as a Library
#####################

************
Installation
************

If you want to use DeTrusty as a library, you can install it from its source code on GitHub or download the package from PyPI.

Requirements
============

DeTrusty is implemented in Python3. The current version of DeTrusty supports Python version 3.7 to 3.11.
DeTrusty uses the ``requests`` library for managing the HTTP(S) requests to the SPARQL endpoints.
The SPARQL parser uses ``ply``.
The generation of the source descriptions from RML mappings is enabled by ``rdflib``.

Local Source Code
=================

You can install DeTrusty from your local source code by performing the following steps.

.. code::

   git clone git@github.com:SDM-TIB/DeTrusty.git
   cd DeTrusty
   python -m pip install -e .

GitHub
======

DeTrusty can also be installed from its source code in GitHub without explicitly cloning the repository:

.. code::

   python -m pip install -e 'git+https://github.com/SDM-TIB/DeTrusty#egg=DeTrusty'

PyPI
====

The easiest way to install DeTrusty is to download the package from PyPI:

.. code::

   python -m pip install DeTrusty
