from rdflib import Namespace

SEMSD = Namespace('https://research.tib.eu/semantic-source-description#')
"""The RDF namespace for the source description ontology."""

def get_query_delete_property_range(endpoint_url: str):
    return '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX semsd: <{semsd}>
    DELETE {{
      ?pred semsd:propertyRange ?pr .
      ?pr ?p ?o .
    }} WHERE {{
      ?pred a rdf:Property ;
        semsd:propertyRange ?pr .
      ?pr a semsd:PropertyRange ;
        semsd:hasSource <{url}> ;
        ?p ?o .
    }}
    '''.format(semsd=SEMSD, url=endpoint_url)

def get_query_delete_source_from_property(endpoint_url: str):
    return '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX semsd: <{semsd}>
    DELETE {{
      ?pred semsd:hasSource <{url}> .
    }} WHERE {{
      ?pred a rdf:Property ;
        semsd:hasSource <{url}> .
    }}
    '''.format(semsd=SEMSD, url=endpoint_url)

def get_query_delete_property_no_source():
    return '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX semsd: <{semsd}>
    DELETE {{
      ?c semsd:hasPredicate ?pred .
      ?pred ?p ?o .
    }} WHERE {{
      ?pred a rdf:Property ;
        ?p ?o .
      FILTER NOT EXISTS {{ ?pred semsd:hasSource ?source }}
      ?c a rdfs:Class ;
        semsd:hasProperty ?pred .
    }}
    '''.format(semsd=SEMSD)

def get_query_delete_source_from_class(endpoint_url: str):
    return '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX semsd: <{semsd}>
    DELETE {{
      ?c semsd:hasSource <{url}> .
    }} WHERE {{
      ?c a rdfs:Class ;
        semsd:hasSource <{url}> .
    }}
    '''.format(semsd=SEMSD, url=endpoint_url)

def get_query_delete_class_no_source():
    return '''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX semsd: <{semsd}>
    DELETE {{
      ?c ?p ?o .
    }} WHERE {{
      ?c a rdfs:Class ;
        ?p ?o .
      FILTER NOT EXISTS {{ ?c semsd:hasSource ?source }}
    }}
    '''.format(semsd=SEMSD)

def get_query_delete_source(endpoint_url: str):
    return '''
    PREFIX semsd: <{semsd}>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    DELETE {{
      ?source ?p ?o .
    }} WHERE {{
      ?source a semsd:DataSource ;
        semsd:hasURL "{url}"^^xsd:anyURI ;
        ?p ?o .
    }}
    '''.format(semsd=SEMSD, url=endpoint_url)
