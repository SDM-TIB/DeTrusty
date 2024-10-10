.. |python| image:: https://img.shields.io/pypi/pyversions/DeTrusty
.. |docker| image:: https://img.shields.io/badge/Docker%20Image-sdmtib/detrusty-blue?logo=Docker
   :target: https://hub.docker.com/r/sdmtib/detrusty

|docker|

#####################
DeTrusty as a Service
#####################

************
Installation
************

If you want to run DeTrusty as a service, you can build the Docker image from its source code or download the Docker image from DockerHub.

Requirements
============

DeTrusty is implemented in Python3. The current version of DeTrusty supports |python|.
DeTrusty uses the ``requests`` library for managing the HTTP(S) requests to the SPARQL endpoints.
The SPARQL parser uses ``ply``.
The generation of the source descriptions from RML mappings is enabled by ``rdflib``.
The Web interface is powered by ``flask`` and the JavaScript library ``YASGUI``.
DeTrusty uses ``gunicorn`` as a Web server.
In order to run DeTrusty as a service, you need to have `Docker <https://docs.docker.com/engine/install/>`_ installed.

Local Source Code
=================

You can install DeTrusty from your local source code by performing the following steps.

.. code:: bash

   git clone git@github.com:SDM-TIB/DeTrusty.git
   cd DeTrusty
   docker build . -t sdmtib/detrusty

DockerHub
=========

The easiest way to install DeTrusty is to download the package from PyPI:

.. code:: bash

   docker pull sdmtib/detrusty:latest

.. NOTE::

   The following examples assume that you cloned the repository, the current working directory is the root directory of the repository, and Docker is installed.

*******************
Setting up DeTrusty
*******************

As stated in the note above, this example assumes that you cloned the repository of DeTrusty, the current working directory is the root directory of the repository, and Docker is installed.
If all that is true, you can start your own instance of DeTrusty by executing the following command.

.. code:: bash

   docker-compose -f example/docker-compose.yml up -d

Creating/Updating Source Descriptions
=====================================

The example loaded the source descriptions for the K4COVID federation.
If you want to update the source descriptions, create a file ``/DeTrusty/Config/endpoints.txt`` inside your Docker container.
This file should contain the URLs to the SPARQL endpoints you want to be included in your federation.
Put one URL per line and execute the following command.

.. code:: bash

   docker exec -it DeTrusty bash -c 'create_rdfmts.py -s /DeTrusty/Config/endpoints.txt'

After the new source description file was generated as ``/DeTrusty/Config/rdfmts.ttl``, you need to restart the ``gunicorn`` workers in order for the changes to take effect.

.. code:: bash

   docker exec -it DeTrusty restart_workers.sh

.. NOTE::

   You can also make use of the more advanced options described in :ref:`creating-source-descriptions`.
   In that case, your endpoints file should contain a JSON string matching with the input of the mentioned examples.
   Additionally, the ``-j`` flag needs to be set.

   .. code:: bash

      docker exec -it DeTrusty bash -c 'create_rdfmts.py -s /DeTrusty/Config/endpoints.json -j'

*************
Web Interface
*************

After setting up DeTrusty as described above, you can start using DeTrusty's Web interface.
In this example, the interface is accessible with the base URL `localhost:5000 <localhost:5000>`_.

.. NOTE::

   Note that the Web interface returns a *"404 - File not found"* if you try to access a route which is not specified.

Web Interface: Executing Queries
================================

Thanks to ``YASGUI``, you can post your queries to DeTrusty from your favorite Web browser by navigating to ``https://your_domain.tld/sparql``, i.e., in this example, use `localhost:5000/sparql <localhost:5000/sparql>`_.
Just enter your query and hit the button.

Web Interface: Plotting Query Plans
===================================

When running DeTrusty as a service, you can also plot the query plan of your queries via the Web interface.
The path is ``https://your_domain.tld/query_plan``, i.e., in this example, it is `localhost:5000/query_plan <localhost:5000/query_plan>`_.
Simply enter your query and hit the button.
The current version of the interface does not allow to specify the decomposition type.
A star-shaped decomposition is assumed for the query plan generation.

***********
RESTful API
***********

DeTrusty also offers an API for executing your queries via POST requests.
The base URL in this example is `localhost:5000 <localhost:5000>`_.

API: DeTrusty Version
=====================

``/version`` returns the version number of DeTrusty.

Example call:

.. code:: bash

   curl -X POST localhost:5000/version

Example output:

.. code:: none

   DeTrusty v0.12.3

API: Executing Queries
======================

``/sparql`` executes the posted SPARQL query and returns the result as a JSON response.

Example call:

.. code:: bash

   curl -X POST -d "query=SELECT DISTINCT ?covidDrug WHERE { ?treatment <http://research.tib.eu/covid-19/vocab/hasCovidDrug> ?covidDrug . } LIMIT 3" localhost:5000/sparql

Example result:

.. code:: JSON

   {
     "cardinality": 3,
     "execution_time": 0.07238245010375977,
     "head": {
       "vars": [
         "covidDrug"
       ]
     },
     "output_version": "2.0",
     "results": {
       "bindings": [
         {
           "__meta__": {
             "is_verified": true
           },
           "covidDrug": {
             "type": "uri",
             "value": "http://research.tib.eu/covid-19/entity/DB00207"
           }
         },
         {
           "__meta__": {
             "is_verified": true
           },
           "covidDrug": {
             "type": "uri",
             "value": "http://research.tib.eu/covid-19/entity/DB00381"
           }
         },
         {
           "__meta__": {
             "is_verified": true
           },
           "covidDrug": {
             "type": "uri",
             "value": "http://research.tib.eu/covid-19/entity/DB00503"
           }
         }
       ]
     }
   }

* ``cardinality`` is the number (integer) of results retrieved
* ``execution_time`` (float) gives the time in seconds the query engine has spent collecting the results
* ``output_version`` (string) indicates the version number of the output format, i.e., to differentiate the current output from possibly changed output in the future
* ``variables`` (list) returns a list of the variables found in the query
* ``result`` is a list of dictionaries containing the results of the query, using the variables as keys;
  metadata about the result verification is included in the key ``__meta__``.
  The current version returns all results as verified as can be seen in the key ``is_verified`` of the metadata.
