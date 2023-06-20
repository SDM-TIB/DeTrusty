#####################
DeTrusty as a Service
#####################

************
Installation
************

If you want to run DeTrusty as a service, you can build the Docker image from its source code or download the Docker image from DockerHub.

Requirements
============

DeTrusty is implemented in Python3. The current version of DeTrusty supports Python version 3.7 to 3.11.
DeTrusty uses the ``requests`` library for managing the HTTP(S) requests to the SPARQL endpoints.
The SPARQL parser uses ``ply``.
The generation of the source descriptions from RML mappings is enabled by ``rdflib``.
The Web interface is powered by ``flask``.
In order to run DeTrusty as a service, you need to have `Docker <https://docs.docker.com/engine/install/>`_ installed.

Local Source Code
=================

You can install DeTrusty from your local source code by performing the following steps.

.. code::

   git clone git@github.com:SDM-TIB/DeTrusty.git
   cd DeTrusty
   docker build . -t sdmtib/detrusty

DockerHub
=========

The easiest way to install DeTrusty is to download the package from PyPI:

.. code::

   docker pull sdmtib/detrusty:latest
