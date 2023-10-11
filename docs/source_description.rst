*******************
Source Descriptions
*******************

In distributed systems, queries are answered by more than one source.
The system needs to decide which source or sources contribute to which part of the query.
Throughout this text the information the distributed system has about the different sources is called *source descriptions*.
There are several approaches when it comes to source descriptions in federations of knowledge graphs.
Some of these approaches are as simple as an index tracking which source is serving which RDF properties.
DeTrusty follows the *RDF Molecule Template* :cite:p:`Endris2018` approach as proposed by Endris et al.

RDF Molecule Templates are a fine-grained description of an RDF dataset as well as its connections with other datasets.
An RDF Molecule corresponds to an RDF class and keeps track which RDF properties are related to the instances of said RDF class.
While this inherently records the domain of the property, the range of the properties is also recorded.
Since an RDF class can be served by more than just one dataset, this information is also encoded in the RDF Molecule Template.
For more information and a formal definition, we refer the reader to :cite:p:`Endris2018`.
See below for an example based on FOAF.

.. code:: JSON

   [
     {
       "rootType": "http://xmlns.com/foaf/0.1/Person",
       "predicates": [
         {
           "predicate": "http://xmlns.com/foaf/0.1/interest",
           "range": [
             "http://xmlns.com/foaf/0.1/Document"
           ]
         },
         {
           "predicate": "http://xmlns.com/foaf/0.1/knows",
           "range": [
             "http://xmlns.com/foaf/0.1/Person"
           ]
         },
         {
           "predicate": "http://xmlns.com/foaf/0.1/name",
           "range": []
         }
       ],
       "linkedTo": [
         "http://xmlns.com/foaf/0.1/Document",
         "http://xmlns.com/foaf/0.1/Person"
       ],
       "wrappers": [
         {
           "url": "http://example.com/sparql",
           "predicates": [
             "http://xmlns.com/foaf/0.1/interest"
           ],
           "urlparam": ""
         },
         {
           "url": "http://private.example.com/sparql",
           "predicates": [
             "http://xmlns.com/foaf/0.1/knows",
             "http://xmlns.com/foaf/0.1/name"
           ],
           "urlparam": {
             "username": "example_user",
             "password": "1234"
           }
         }
       ]
     },
     {
       "rootType": "http://xmlns.com/foaf/0.1/Document",
       "predicates": [
         {
           "predicate": "http://xmlns.com/foaf/0.1/topic",
           "range": []
         }
       ],
       "linkedTo": [],
       "wrappers": [
         {
           "url": "http://example.com/sparql",
           "predicates": [
             "http://xmlns.com/foaf/0.1/topic"
           ],
           "urlparam": ""
         }
       ]
     }
   ]