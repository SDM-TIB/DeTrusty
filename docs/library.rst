.. |python| image:: https://img.shields.io/pypi/pyversions/DeTrusty
.. |format| image:: https://img.shields.io/pypi/format/DeTrusty
.. |status| image:: https://img.shields.io/pypi/status/DeTrusty
.. |version| image:: https://img.shields.io/pypi/v/DeTrusty
   :target: https://pypi.org/project/DeTrusty

|python| |format| |status| |version|

#####################
DeTrusty as a Library
#####################

************
Installation
************

If you want to use DeTrusty as a library, you can install it from its source code on GitHub or download the package from PyPI.

Requirements
============

DeTrusty is implemented in Python3. The current version of DeTrusty supports |python|.
DeTrusty uses the ``requests`` library for managing the HTTP(S) requests to the SPARQL endpoints.
The SPARQL parser uses ``ply``.
The generation of the source descriptions from RML mappings is enabled by ``rdflib``.

Local Source Code
=================

You can install DeTrusty from your local source code by performing the following steps.

.. code:: bash

   git clone git@github.com:SDM-TIB/DeTrusty.git
   cd DeTrusty
   python -m pip install -e .

GitHub
======

DeTrusty can also be installed from its source code in GitHub without explicitly cloning the repository:

.. code:: bash

   python -m pip install -e 'git+https://github.com/SDM-TIB/DeTrusty#egg=DeTrusty'

PyPI
====

The easiest way to install DeTrusty is to download the package from PyPI:

.. code:: bash

   python -m pip install DeTrusty

*****************
Executing Queries
*****************

.. NOTE::

   The goal of this section is to explain how to run SPARQL queries when using DeTrusty as a library.
   We refer the reader to the chapter :doc:`/source_description` for more information about what source descriptions are and why they are needed.
   Additionally, we refer to :doc:`/decomposition` for more details about what decomposition is and an overview of different decomposition types.

DeTrusty offers the function ``run_query`` for executing SPARQL queries.

.. automodule:: DeTrusty
   :noindex:
   :members: run_query

Additionally, DeTrusty offers the function ``get_config`` to create an object with the internal representation of the source descriptions.

.. automodule:: DeTrusty.Molecule.MTManager
   :noindex:
   :members: get_config

Knowledge4COVID-19
==================

In order to gain hands-on experience with DeTrusty, we provide a couple of examples.
This particular example uses the queries related to the Knowledge4COVID-19 KG :cite:p:`Sakor2023`.
Before running the examples below, please, make sure that you have DeTrusty installed.

The federation of knowledge graphs for this example contains the following SPARQL endpoints:

* Knowledge4COVID-19 KG: https://labs.tib.eu/sdm/covid19kg/sparql
* DBpedia: https://dbpedia.org/sparql
* Wikidata: https://query.wikidata.org/sparql

Q1. COVID-19 Drugs for Patients with Asthma
-------------------------------------------

*"Retrieve from DBpedia the excretion rate, metabolism, and routes of administration of the COVID-19 drugs in the treatments to treat COVID-19 in patients with Asthma."*

.. literalinclude:: ../example/K4COVID/Q1.rq
   :language: sparql

This query collects data from the Knowledge4COVID-19 KG and DBpedia. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/Q1.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

Q2. COVID-19 Drugs for Patients with a Cardiopathy
--------------------------------------------------

*"Retrieve from Wikidata the CheMBL code, metabolism, and routes of administration of the COVID-19 drugs in the treatments to treat COVID-19 in patients with a cardiopathy."*

.. literalinclude:: ../example/K4COVID/Q2.rq
   :language: sparql

This query collects data from the Knowledge4COVID-19 KG and Wikidata. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/Q2.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

Q3. Detailed COVID-19 Drug Information for Patients with Asthma
---------------------------------------------------------------

*"Retrieve from DBpedia the excretion rate, metabolism, and routes of administration, CheMBL and Kegg codes, smile notation, and trade name of the COVID-19 drugs in the treatments to treat COVID-19 in patients with Asthma."*

.. literalinclude:: ../example/K4COVID/Q3.rq
   :language: sparql

This query collects data from the Knowledge4COVID-19 KG and DBpedia. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/Q3.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

Q4. COVID-19 Comorbidity Information
------------------------------------

*"Retrieve from DBpedia the disease label, ICD-10 and mesh codes, and risks of the comorbidities of the COVID-19 treatments."*

.. literalinclude:: ../example/K4COVID/Q4.rq
   :language: sparql

This query collects data from the Knowledge4COVID-19 KG and Wikidata. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/Q4.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

Q5. COVID-19 Comorbidity Drugs
------------------------------

*"Retrieve the COVID-19 and comorbidity drugs on a treatment and the CheMBL code, mass, and excretion route for the comorbidity drugs."*

.. literalinclude:: ../example/K4COVID/Q5.rq
   :language: sparql

This query collects data from the Knowledge4COVID-19 KG, DBpedia, and Wikidata. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/K4COVID/Q5.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

CoyPu
=====

This particular example uses queries related to the project `CoyPu <https://coypu.org>`_.
Before running the examples below, please, make sure that you have DeTrusty installed.

The federation of knowledge graphs for this example contains the following SPARQL endpoints:

* World Bank KG: https://labs.tib.eu/sdm/worldbank_endpoint/sparql
* Wikidata: https://query.wikidata.org/sparql

Q1. Life Expectancy in 2017
---------------------------

*"Retrieve the life expectancy for all countries in 2017 as reported by World Bank and Wikidata"*

.. literalinclude:: ../example/CoyPu/Q1.rq
   :language: sparql

This query collects data from the World Bank KG and Wikidata. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/CoyPu/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/CoyPu/Q1.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

Q2. GDP and CO2 Emission per Capita in Germany
----------------------------------------------

*"Retrieve the GDP per capita and carbon emission per capita for Germany per year."*

.. literalinclude:: ../example/CoyPu/Q2.rq
   :language: sparql

This query collects data from the World Bank KG and Wikidata. See below how to execute the query with DeTrusty.

.. code:: python

   from DeTrusty import get_config, run_query

   config = get_config('https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/CoyPu/rdfmts.ttl')
   query = 'https://raw.githubusercontent.com/SDM-TIB/DeTrusty/master/example/CoyPu/Q2.rq'
   result = run_query(query, config=config, join_stars_locally=False)
   print(result)

.. _creating-source-descriptions:

****************************
Creating Source Descriptions
****************************

.. NOTE::

   The goal of this section is to explain how to create the source descriptions when using DeTrusty as a library.
   We refer the reader to the chapter :doc:`/source_description` for more information about what source descriptions are and why they are needed.

DeTrusty offers the function ``create_rdfmts`` for the source description creation.

.. automodule:: DeTrusty.Molecule.MTCreation
    :noindex:
    :members: create_rdfmts

The remainder of this section provides examples showing how to use the function in different scenarios.

* `Standard Case`_: public SPARQL endpoints only
* `Private Endpoints`_: including private endpoints requiring authentication into the federation
* `Source Descriptions from RML Mappings`_: use RML mappings to compute the source descriptions
* `Restricting Classes of an Endpoint`_: consider only specific classes of an endpoint

Standard Case
=============

The standard case is to include only public SPARQL endpoints in the federation, collect the source description via SPARQL queries, and consider all classes in the endpoints.
The following code snippet collects the source description of two public endpoints and saves it in the file ``./Config/rdfmts.ttl``.

.. code:: python

    from DeTrusty.Molecule.MTCreation import create_rdfmts

    endpoints = ['http://url_to_endpoint_1', 'https://url_to_endpoint_2:port/sparql']
    create_rdfmts(endpoints, './Config/rdfmts.ttl')

**Alternatively,** ``None`` can be passed instead of a path.
In that case, ``create_rdfmts`` returns the source description in DeTrusty's internal structure.
This is helpful if several queries are to be executed in order to avoid reading the source description from a file prior to executing each query.

.. code-block:: python
    :emphasize-lines: 4

    from DeTrusty.Molecule.MTCreation import create_rdfmts

    endpoints = ['http://url_to_endpoint_1', 'https://url_to_endpoint_2:port/sparql']
    config = create_rdfmts(endpoints, None)  # returns the configuration instead of writing it to a file

**Additionally,** the source description object provides a method for saving it to a file.

.. code:: python

   config.saveToFile('/path/for/new_mts')


Private Endpoints
=================

Starting with version 0.6.0, DeTrusty can handle private endpoints that require authentication.
Currently, basic authentication with Base64 encoding as well as token-based authentication via a token server are supported.
In the case of token-based authentication, DeTrusty expects the token server to return the token in the response field ``access_token``.
Additionally, DeTrusty expects the lifespan of the token in seconds to be returned in the field ``expires_in``.
The configuration changes slightly compared to the standard case:

.. code-block:: python
    :emphasize-lines: 4-8

    from DeTrusty.Molecule.MTCreation import create_rdfmts

    endpoints = {
      'https://url_to_endpoint_1': {
        'keycloak': 'https://url_to_token_server',
        'username': 'YOUR_USERNAME',
        'password': 'YOUR_PASSWORD'
      }
    }
    create_rdfmts(endpoints, './Config/rdfmts.ttl')

The keys of ``endpoints`` are the URLs of the SPARQL endpoints.
Each endpoint is represented as a dictionary itself; holding all parameters in the form of (key, value) pairs.
``keycloak`` is the URL to the token server, ``username`` and ``password`` represent the credentials for the token server or SPARQL endpoint.

.. NOTE::

   If your SPARQL endpoint uses basic authentication with Base64 encoding instead of a token server, simply omit ``keycloak``.

Source Descriptions from RML Mappings
=====================================

Starting with version 0.6.0, DeTrusty can collect the metadata necessary for source selection and decomposition from RML mappings.
Collecting metadata from RML mappings instead of the SPARQL endpoint considerably increases the performance of the metadata collection process.
Of course, this is only feasible for endpoints that were created using RML mappings.

.. code-block:: python
    :emphasize-lines: 4-9

    from DeTrusty.Molecule.MTCreation import create_rdfmts

    endpoints = {
      'https://url_to_endpoint_1': {
        'mappings': [
          'path/to/mapping/file1',
          'path/to/mapping/file2'
        ]
      }
    }
    create_rdfmts(endpoints, './Config/rdfmts.ttl')

The key ``mappings`` holds a list of paths to the mapping files that were used to create the RDF data served by the SPARQL endpoint.

Restricting Classes of an Endpoint
==================================

Starting with version 0.7.0, DeTrusty can restrict the collection of metadata to specific classes of an endpoint.

.. WARNING::

   The classes that are to be included in the source description creation process need to be specified using their **full URIs**.

.. code-block:: python
    :emphasize-lines: 4-9

    from DeTrusty.Molecule.MTCreation import create_rdfmts

    endpoints = {
      'https://url_to_endpoint_1': {
        'types': [
          'http://example.com/ontology/ClassA',
          'http://example.com/ontology/ClassB'
        ]
      }
    }
    create_rdfmts(endpoints, './Config/rdfmts.ttl')

The key ``types`` holds a list of all the classes of the endpoint that should be considered for the source description creation process.
