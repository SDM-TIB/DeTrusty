*******************
Source Descriptions
*******************

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
