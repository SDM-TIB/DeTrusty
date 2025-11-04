###################
Source Descriptions
###################

In distributed systems, queries are answered by more than one source.
The system needs to decide which source or sources contribute to which part of the query.
Throughout this text the information the distributed system has about the different sources is called *source descriptions*.
There are several approaches when it comes to source descriptions in federations of knowledge graphs.
Some of these approaches are as simple as an index tracking which source is serving which RDF properties.
DeTrusty follows a similar approach as the *RDF Molecule Template* :cite:p:`Endris2018` proposed by Endris et al.
However, DeTrusty uses *semantic source descriptions*, i.e., they are described in RDF themselves.

The semantic source descriptions are a fine-grained description of an RDF dataset as well as its connections with other datasets.
An RDF class keeps track which RDF properties are related to the instances of said RDF class.
While this inherently records the domain of the property, the range of the properties is also recorded.
Since an RDF class can be served by more than just one dataset, this information is also encoded.
See below for an example based on FOAF.

.. code:: turtle

   @prefix foaf: <http://xmlns.com/foaf/0.1/> .
   @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
   @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
   @prefix semsd: <https://research.tib.eu/semantic-source-description#> .
   @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

   foaf:Document a rdfs:Class ;
       semsd:hasProperty foaf:topic ;
       semsd:hasSource <http://example.com/sparql> .

   foaf:Person a rdfs:Class ;
       semsd:hasProperty foaf:interest,
           foaf:knows,
           foaf:name ;
       semsd:hasSource <http://example.com/sparql>,
           <http://private.example.com/sparql> .

   foaf:interest a rdf:Property ;
       semsd:hasSource <http://example.com/sparql> ;
       semsd:propertyRange [
           a semsd:PropertyRange ;
           semsd:hasSource <http://example.com/sparql> ;
           rdfs:domain foaf:Person ;
           rdfs:range foaf:Document
       ] .

   foaf:knows a rdf:Property ;
       semsd:hasSource <http://private.example.com/sparql> ;
       semsd:propertyRange [
           a semsd:PropertyRange ;
           semsd:hasSource <http://example.com/sparql> ;
           rdfs:domain foaf:Person ;
           rdfs:range foaf:Person
       ] .

   foaf:name a rdf:Property ;
       semsd:hasSource <http://private.example.com/sparql> .

   foaf:topic a rdf:Property ;
       semsd:hasSource <http://example.com/sparql> .

   <http://private.example.com/sparql> a semsd:DataSource ;
      semsd:hasURL "http://private.example.com/sparql"^^xsd:anyURI ;
      semsd:username "privateuser" ;
      semsd:password "password" .

   <http://example.com/sparql> a semsd:DataSource ;
       semsd:hasURL "http://example.com/sparql"^^xsd:anyURI .

.. _creating-source-descriptions:

****************************
Creating Source Descriptions
****************************

The goal of this section is to explain how to create the source descriptions for DeTrusty.
DeTrusty offers the function ``create_rdfmts`` for the source description creation.

.. automodule:: DeTrusty.Molecule.MTCreation
    :noindex:
    :members: create_rdfmts

The remainder of this section provides examples showing how to use the function in different scenarios.

* `Standard Case`_: public SPARQL endpoints only
* `Private Endpoints`_: including private endpoints requiring authentication into the federation
* `Source Descriptions from RML Mappings`_: use RML mappings to compute the source descriptions
* `Restricting Classes of an Endpoint`_: consider only specific classes of an endpoint
* `Managing Federations`_: managing multiple federations of endpoints

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

Managing Federations
====================

Starting from version 0.22.0, DeTrusty supports the management of multiple federations within the same source description file/endpoint.
For the creation of a queryable endpoint from a source description file, DeTrusty resorts to `Pyoxigraph`.
`Virtuoso` SPARQL endpoints are also supported.

.. code-block:: python

    from DeTrusty import get_config, run_query
    from DeTrusty.Molecule.MTManager import FederationConfig

    config = get_config('federations.ttl')  # regular source description file
    fed_config = FederationConfig(config, 'http://example.com/fed1#')  # limiting to specific federation

    # Adding endpoints
    fed_config.add_endpoint('https://url_to_endpoint_1')
    fed_config.add_endpoint('https://url_to_endpoint_2')
    fed_config.add_endpoint('https://url_to_endpoint_3')

    # Running query over the federation
    query = "SELECT DISTINCT ?c WHERE { ?s a ?c }"
    result = run_query(query, config=fed_config)

    # Deleting an endpoint
    fed_config.delete_endpoint('https://url_to_endpoint_3')

Naturally, you can create several _FederationConfig_ objects for all the different federations required in your application.