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

*******************
Source Descriptions
*******************

We refer the reader to the chapter :doc:`/source_description` for more information about what source descriptions are, why they are needed, and how they can be created.
A detailed explanation of how to create the source descriptions is given in :ref:`creating-source-descriptions`.
