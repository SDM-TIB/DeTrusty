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
The source descriptions are stored and queried using ``pyoxigraph``, an embedded RDF store.
The Web interface is powered by ``flask``, the JavaScript library ``YASGUI``, and ``d3`` for rendering query plans.
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
If you want to update the source descriptions, you need to update the file ``/DeTrusty/Config/rdfmts.ttl`` inside your Docker container.
See :ref:`creating-source-descriptions` for how to create said file.
After the new source description file was generated as ``/DeTrusty/Config/rdfmts.ttl``, you need to reload the metadata service in order for the changes to take effect.

.. code:: bash

   docker exec -it detrusty restart_metadata_service.sh

This sends a ``SIGHUP`` to the metadata service's ``gunicorn`` process, which triggers a graceful reload of its workers without dropping any in-flight requests.

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

If more than one federation is available, a federation selector bar will appear automatically above the query editor.
Selecting a federation restricts source selection to the endpoints registered under that named graph.
If no federation is selected, DeTrusty queries across all available endpoints.

Web Interface: Plotting Query Plans
===================================

When running DeTrusty as a service, you can also plot the query plan of your queries via the Web interface.
The path is ``https://your_domain.tld/query_plan``, i.e., in this example, it is `localhost:5000/query_plan <localhost:5000/query_plan>`_.
Simply enter your query and hit the button.
The current version of the interface does not allow to specify the decomposition type.
A star-shaped decomposition is assumed for the query plan generation.

As with the query editor, a federation selector bar is shown automatically when more than one federation is available.

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

The optional ``federation`` parameter restricts source selection to the endpoints registered under the given named graph URI.
If omitted, DeTrusty queries across all available endpoints.

Example call (all federations):

.. code:: bash

   curl -X POST -d "query=SELECT DISTINCT ?covidDrug WHERE { ?treatment <http://research.tib.eu/covid-19/vocab/hasCovidDrug> ?covidDrug . } LIMIT 3" localhost:5000/sparql

Example call (specific federation):

.. code:: bash

   curl -X POST -d "query=SELECT DISTINCT ?covidDrug WHERE { ?treatment <http://research.tib.eu/covid-19/vocab/hasCovidDrug> ?covidDrug . } LIMIT 3" \
        -d "federation=https://research.tib.eu/semantic-source-description#K4COVID" \
        localhost:5000/sparql

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

API: Listing Federations
========================

``/federations`` returns the named graphs (federations) registered in the metadata store.
The response is used by the Web interface to populate the federation selector, but can also be called directly.

Example call:

.. code:: bash

   curl -X GET localhost:5000/federations

Example output:

.. code:: JSON

   {
     "federations": [
       "https://research.tib.eu/semantic-source-description#CoyPu",
       "https://research.tib.eu/semantic-source-description#K4COVID"
     ]
   }

***************************
RESTful API: Administration
***************************

The following endpoints allow managing the federations and their endpoints at runtime.
They require an admin Bearer token to be set via the ``FEDERATION_ADMIN_KEY`` environment variable.
All requests must carry the header ``Authorization: Bearer <FEDERATION_ADMIN_KEY>``.

.. WARNING::

   If ``FEDERATION_ADMIN_KEY`` is not configured, all administration endpoints return ``403 Forbidden`` and federation management is disabled.

API: Adding an Endpoint to a Federation
========================================

``POST /federation/endpoint`` registers a new SPARQL endpoint with the metadata service.

Parameters:

* ``endpoint`` *(required)* — URL of the SPARQL endpoint to add.
* ``federation`` *(optional)* — Named graph URI to add the endpoint to. If omitted, the endpoint is added to the default (global) configuration.
* ``username`` *(optional)* — Username for authenticated endpoints.
* ``password`` *(optional)* — Password for authenticated endpoints.
* ``keycloak`` *(optional)* — Token server URL for Keycloak-protected endpoints.

Example call:

.. code:: bash

   curl -X POST \
        -H "Authorization: Bearer mysecretkey" \
        -d "endpoint=https://example.org/sparql" \
        -d "federation=https://research.tib.eu/semantic-source-description#K4COVID" \
        localhost:5000/federation/endpoint

Example output:

.. code:: JSON

   {"status": "ok", "endpoint": "https://example.org/sparql"}

API: Removing an Endpoint from a Federation
============================================

``DELETE /federation/endpoint`` removes a SPARQL endpoint from the metadata service.

Parameters:

* ``endpoint`` *(required)* — URL of the SPARQL endpoint to remove.
* ``federation`` *(optional)* — Named graph URI from which to remove the endpoint. If omitted, the endpoint is removed from the default (global) configuration.

Example call:

.. code:: bash

   curl -X DELETE \
        -H "Authorization: Bearer mysecretkey" \
        -d "endpoint=https://example.org/sparql" \
        -d "federation=https://research.tib.eu/semantic-source-description#K4COVID" \
        localhost:5000/federation/endpoint

Example output:

.. code:: JSON

   {"status": "ok", "endpoint": "https://example.org/sparql"}

API: Querying the Metadata Store
=================================

``/federation/sparql`` forwards a SPARQL query directly to the metadata service, allowing inspection of the stored source descriptions.
Both ``GET`` and ``POST`` are supported.

Example call:

.. code:: bash

   curl -X POST \
        -H "Authorization: Bearer mysecretkey" \
        -d "query=SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }" \
        localhost:5000/federation/sparql
