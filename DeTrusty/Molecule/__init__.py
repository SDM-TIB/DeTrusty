from rdflib import Namespace

SEMSD = Namespace('https://research.tib.eu/semantic-source-description#')
"""The RDF namespace for the source description ontology."""

DEFAULT_GRAPH = SEMSD + 'defaultGraph'
"""The default RDF graph to use for querying."""
