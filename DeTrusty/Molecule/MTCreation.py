from __future__ import annotations

__author__ = 'Philipp D. Rohde and Kemele M. Endris'

import logging
import multiprocessing
import sys
from queue import Queue
from time import time
from typing import Optional

from pyoxigraph import Literal as oxiLiteral
from pyoxigraph import Quad, NamedNode, BlankNode
from rdflib import Graph, URIRef, BNode, Literal, RDF, RDFS, XSD

from DeTrusty.Logger import get_logger
from DeTrusty.Molecule import SEMSD
from DeTrusty.Molecule.MTManager import MTCreationConfig, TTLConfig
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger('rdfmts', '.rdfmts.log', file_and_console=True)

CONFIG = MTCreationConfig()
DEFAULT_OUTPUT_PATH = '/DeTrusty/Config/rdfmts.ttl'
TYPING_WIKIDATA = '<http://www.wikidata.org/prop/direct/P31>'

metas = [
    'http://www.w3.org/ns/sparql-service-description',
    'http://www.openlinksw.com/schemas/virtrdf#',
    'http://www.w3.org/2000/01/rdf-schema#',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'http://purl.org/dc/terms/Dataset',
    'http://www.w3.org/2002/07/owl#',
    'http://www.w3.org/2001/XMLSchema#',
    'nodeID://'
]


class Endpoint:
    """Simple representation of an endpoint. URL is mandatory, but an endpoint might have optional parameters."""
    def __init__(self, url: str, params: dict = None, is_pyoxigraph: bool = False):
        self.url = url
        self.params = params if params is not None else {}
        self.is_pyoxigraph = is_pyoxigraph

    @property
    def types(self):
        return self.params.get('types', [])

    @property
    def triples(self):
        triples = set()
        if self.is_pyoxigraph:
            triples.add(Quad(NamedNode(self.url), NamedNode(RDF.type), NamedNode(SEMSD.DataSource), None))
            triples.add(Quad(NamedNode(self.url), NamedNode(SEMSD.hasURL), oxiLiteral(self.url, datatype=NamedNode(XSD.anyURI)), None))
        else:
            triples.add((URIRef(self.url), RDF.type, SEMSD.DataSource))
            triples.add((URIRef(self.url), SEMSD.hasURL, Literal(self.url, datatype=XSD.anyURI)))
        if 'username' in self.params.keys():
            if self.is_pyoxigraph:
                triples.add(Quad(NamedNode(self.url), NamedNode(SEMSD.username), oxiLiteral(self.params['username']), None))
            else:
                triples.add((URIRef(self.url), SEMSD.username, Literal(self.params['username'])))
        if 'password' in self.params.keys():
            if self.is_pyoxigraph:
                triples.add(Quad(NamedNode(self.url), NamedNode(SEMSD.password), oxiLiteral(self.params['password']), None))
            else:
                triples.add((URIRef(self.url), SEMSD.password, Literal(self.params['password'])))
        if 'keycloak' in self.params.keys():
            if self.is_pyoxigraph:
                triples.add(Quad(NamedNode(self.url), NamedNode(SEMSD.tokenServer), oxiLiteral(self.params['keycloak']), None))
            else:
                triples.add((URIRef(self.url), SEMSD.tokenServer, Literal(self.params['keycloak'])))
        return triples


def create_rdfmts(endpoints: list | dict,
                  output: Optional[str] = DEFAULT_OUTPUT_PATH) -> Optional[TTLConfig]:

    """Generating rdfmts.ttl, which need to be supplied during query execution using run_query

    Parameters
    ----------
    endpoints : list or dict
        The endpoints from which information will be collected.
    output : str, optional
        Path for the generated configuration to be saved at.

        * If not provided: default path will be used, i.e. path/to/DeTrusty-installation/Config/rdfmts.ttl'
        * In case of None: the config will not be saved, instead a TTLConfig object is returned.

    Return
    ------
    TTLConfig, optional
        Only generating return value when output=None, else a file with the configuration is saved
        at the location provided with the parameter output.

    """
    logger_wrapper = get_logger('DeTrusty.Wrapper.RDFWrapper')
    logger_wrapper.setLevel(logging.WARNING)  # temporarily disable logging of contacting the source

    if output is not None:
        try:
            with open(output, 'a') as f:
                if not f.writable():
                    raise PermissionError
        except FileNotFoundError as e:
            logger.critical('No such file or directory: ' + output + '\tMake sure the directory exists!')
            raise e
        except PermissionError as e:
            logger.critical('You may not have permissions to open or write to the file: ' + output +
                            '\tPlease, check your permissions!')
            raise e

    graph = Graph()
    graph.bind('semsd', SEMSD)
    eoffs = {}
    epros = []
    start = time()

    CONFIG.setEndpoints(endpoints)

    endpoints = [Endpoint(key, value) for key, value in CONFIG.endpoints.items()]
    endpoints = _accessible_endpoints(endpoints, exit_on_error=True)
    if len(endpoints) == 0:
        logger.critical('None of the endpoints can be accessed. Please check if you write URLs properly!')
        sys.exit(1)
    for e in endpoints:
        [graph.add(triple) for triple in e.triples]
        tq = multiprocessing.Queue()
        eoffs[e.url] = tq
        p1 = multiprocessing.Process(target=_collect_rdfmts_from_source, args=(e, tq,))
        epros.append(p1)
        p1.start()

    while len(eoffs) > 0:
        for url in eoffs:
            result_queue = eoffs[url]
            triples = result_queue.get()
            [graph.add(triple) for triple in triples]
            del eoffs[url]
            break
    for p in epros:
        if p.is_alive():
            p.terminate()

    duration = time() - start
    logger.info('----- DONE in ' + str(duration) + ' seconds!-----')
    logger_wrapper.setLevel(logging.INFO)  # reset the logger
    if output is not None:
        graph.serialize(output, format='turtle', encoding='utf8')
    else:
        return TTLConfig(graph.serialize(None, format='turtle', encoding='utf8'))


def _collect_rdfmts_from_source(endpoint: Endpoint, tq):
    # get the typed concepts, predicates, etc. for one source
    if 'mappings' in endpoint.params:
        triples, classes, template_classes = get_rdfmts_from_mapping(endpoint)
        if template_classes:
            # get metadata for classes that use a template from the endpoint
            triples = triples.union(get_rdfmts_from_endpoint(endpoint, ignore_classes=classes))
    else:
        triples = get_rdfmts_from_endpoint(endpoint)
    tq.put(triples)
    tq.put('EOF')
    return triples


def get_rdfmts_from_endpoint(endpoint: Endpoint, ignore_classes=None):
    concepts = _get_typed_concepts(endpoint)
    source = endpoint.url
    logger.info(source + ': ' + str(concepts))
    if ignore_classes is not None:
        logger.info(source + ' ignoring classes: ' + str(ignore_classes))
        concepts = [c for c in concepts if c not in ignore_classes]
        logger.info(source + ' considering only: ' + str(concepts))
    triples = set()
    for c in concepts:
        if '^^' in c:
            continue
        logger.info(c)
        triples = triples.union(_triples_class(c, source, is_pyoxigraph=endpoint.is_pyoxigraph))
        predicates = _get_predicates(endpoint, c)
        for p in predicates:
            if 'wikiPageWikiLink' in p:
                continue
            triples = triples.union(_triples_predicate(p, c, source, is_pyoxigraph=endpoint.is_pyoxigraph))
            ranges_ = _get_predicate_range(endpoint, c, p)
            for range_ in ranges_:
                triples = triples.union(_triples_predicate_range(p, c, range_, source, is_pyoxigraph=endpoint.is_pyoxigraph))

    logger.info('=================================')
    return triples


def _get_typed_concepts(endpoint):
    if endpoint.types:
        return endpoint.types

    query = 'SELECT DISTINCT ?t WHERE { ?s '
    if 'wikidata' in endpoint.url:
        query += TYPING_WIKIDATA
    else:
        query += 'a'
    query += ' ?t . }'
    res_list, _ = _get_results_iter(query, endpoint, 't')
    return [r for r in res_list if True not in [m in str(r) for m in metas]]


def _get_predicates(endpoint, type_):
    query = 'SELECT DISTINCT ?p WHERE { ?s '
    if 'wikidata' in endpoint.url:
        query += TYPING_WIKIDATA
    else:
        query += 'a'
    query += ' <' + type_ + '> . ?s ?p ?pt . }'
    res_list, status = _get_results_iter(query, endpoint, 'p')

    if status == -1:  # fallback - get predicates from randomly selected instances of the type
        logger.warn('giving up on ' + query)
        logger.warn('trying instances...')
        rand_inst_res = _get_predicates_of_random_instances(endpoint, type_)
        for pred in rand_inst_res:
            if pred not in res_list:
                res_list.append(pred)

    return res_list


def _get_predicates_of_random_instances(endpoint, type_):
    query = 'SELECT DISTINCT ?s WHERE { ?s '
    if 'wikidata' in endpoint.url:
        query += TYPING_WIKIDATA
    else:
        query += 'a'
    query += ' <' + type_ + '> . }'
    res_list, _ = _get_results_iter(query, endpoint, 's', limit=100, max_tries=100, max_answers=100)
    results = []
    batches = [res_list[i:i+10] for i in range(0, len(res_list), 10)]
    for batch in batches:
        batch = ['<' + r + '>' for r in batch]
        query = 'SELECT DISTINCT ?p WHERE {\n' \
                '  VALUES ?s { ' + ' '.join(batch) + ' }\n' \
                '  ?s ?p ?pt\n}'
        res_list_batch, _ = _get_results_iter(query, endpoint, 'p')
        results.extend([r for r in res_list_batch])
    return list(set(results))


def _get_predicate_range(endpoint, type_, predicate):
    # first, get the range using rdfs:range
    query = 'SELECT DISTINCT ?range WHERE { <' + predicate + '> <http://www.w3.org/2000/01/rdf-schema#range> ?range . }'
    res_list, _ = _get_results_iter(query, endpoint, 'range')
    ranges = [r for r in res_list if True not in [m in str(r) for m in metas]]

    # second, get range from instances
    query = 'SELECT DISTINCT ?range WHERE {\n' \
            '  ?s '
    if 'wikidata' in endpoint.url:
        query += TYPING_WIKIDATA
    else:
        query += 'a'
    query += ' <' + type_ + '> .\n' \
             '  ?s <' + predicate + '> ?pt .\n' \
             '  ?pt a ?range .\n}'
    res_list, _ = _get_results_iter(query, endpoint, 'range')
    ranges.extend([r for r in res_list if True not in [m in str(r) for m in metas]])

    return list(set(ranges))


def _accessible_endpoints(endpoints, exit_on_error=False):
    ask = 'ASK { ?s ?p ?o }'
    accessible_endpoints = []
    for e in endpoints:
        url = e.url
        val, c = contact_source(url, ask, Queue(), CONFIG)
        if c == -2:
            logger.error(url + ' --> is not accessible. Please check if this endpoint properly started!')
            if exit_on_error:
                sys.exit(1)
        if val:
            accessible_endpoints.append(e)
        else:
            logger.info(url + ' --> is returning empty results. Hence, will not be included in the federation!')

    return accessible_endpoints


def _get_results_iter(query: str, endpoint: Endpoint, return_variable: str, limit: int = -1,
                      max_tries: int = -1, max_answers: int = -1):
    offset = 0
    res_list = []
    status = 0
    num_requests = 0

    if limit == -1:
        limit = 10000

    while True:
        query_copy = query + ' LIMIT ' + str(limit) + (' OFFSET ' + str(offset) if offset > 0 else '')
        num_requests += 1
        res_queue = Queue()
        _, card = contact_source(endpoint.url, query_copy, res_queue, CONFIG)

        # if receiving the answer fails, try with a decreasing limit
        if card == -2:
            limit = limit // 2
            if limit < 1:
                status = -1
                break
            continue

        # results returned from the endpoint need to be appended to the result list
        if card > 0:
            res = res_queue.get()
            while res != 'EOF':
                if res[return_variable]['type'] == 'uri':
                    res_list.append(res[return_variable]['value'])
                    res = res_queue.get()

        # stop if all results are retrieved or the maximum number of tries is reached
        if card < limit or (0 < max_answers <= len(res_list)) or num_requests == max_tries:
            break

        offset += limit

    return res_list, status

def get_rdfmts_from_mapping(endpoint: Endpoint):
    source = endpoint.url
    mapping_graph = Graph()
    for mapping_file in endpoint.params['mappings']:
        mapping_graph.parse(mapping_file, format='n3')

    ask = 'PREFIX rr: <http://www.w3.org/ns/r2rml#>\n' \
          'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n' \
          'ASK {\n' \
          '  ?tm rr:predicateObjectMap ?sm .\n' \
          '  ?sm rr:predicate rdf:type .\n' \
          '  ?sm rr:objectMap ?smo .\n' \
          '  ?smo rr:template ?t .\n' \
          '  FILTER(regex(str(?t), "{.*}"))\n' \
          '}'
    template_classes = mapping_graph.query(ask).askAnswer

    query = 'PREFIX rr: <http://www.w3.org/ns/r2rml#>\n' \
            'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\n' \
            'SELECT DISTINCT ?t ?p ?r WHERE {\n' \
            '  {\n' \
            '    ?tm rr:subjectMap  ?sm .\n' \
            '    ?sm rr:class ?t .\n' \
            '    ?tm rr:predicateObjectMap ?pom .\n' \
            '    ?pom rr:predicate ?p .\n' \
            '    OPTIONAL {\n' \
            '      ?pom rr:objectMap ?om .\n' \
            '      ?om rr:parentTriplesMap ?pt .\n' \
            '      ?pt rr:subjectMap ?ptsm .\n' \
            '      ?ptsm rr:class ?r .\n' \
            '    }\n' \
            '  }\n' \
            '  UNION\n' \
            '  {\n' \
            '    ?tm rr:predicateObjectMap ?sm .\n' \
            '    ?sm rr:predicate rdf:type .\n' \
            '    ?sm rr:objectMap ?smo .\n' \
            '    ?smo rr:template|rr:constant ?t .\n' \
            '    FILTER(!regex(str(?t), "{.*}"))\n' \
            '    ?tm rr:predicateObjectMap ?pom .\n' \
            '    ?pom rr:predicate ?p .\n' \
            '    OPTIONAL {\n' \
            '      ?pom rr:objectMap ?om .\n' \
            '      ?om rr:parentTriplesMap ?pt .\n' \
            '      ?pt rr:subjectMap ?ptsm .\n' \
            '      ?ptsm rr:class ?r .\n' \
            '    }\n' \
            '  }\n' \
            '} ORDER BY ?t ?p ?r'

    res = mapping_graph.query(query)
    classes = set()
    triples = set()
    for r in res:
        class_ = str(r['t'])
        classes.add(class_)
        triples = triples.union(_triples_class(class_, source))
        triples = triples.union(_triples_predicate(RDF.type.toPython(), class_, source))

        predicate = str(r['p'])
        triples = triples.union(_triples_predicate(predicate, class_, source))
        range_ = str(r['r']) if r['r'] is not None else None
        if range_ is not None:
            triples.union(_triples_predicate_range(predicate, class_, range_, source))

    return triples, classes, template_classes

def _triples_class(class_, source, is_pyoxigraph=False):
    c = set()
    if is_pyoxigraph:
        c.add(Quad(NamedNode(class_), NamedNode(RDF.type), NamedNode(RDFS.Class), None))
        c.add(Quad(NamedNode(class_), NamedNode(SEMSD.hasSource), NamedNode(source), None))
    else:
        c.add((URIRef(class_), RDF.type, RDFS.Class))
        c.add((URIRef(class_), SEMSD.hasSource, URIRef(source)))
    return c

def _triples_predicate(predicate, class_, source, is_pyoxigraph=False):
    pred = set()
    if is_pyoxigraph:
        pred.add(Quad(NamedNode(predicate), NamedNode(RDF.type), NamedNode(RDF.Property), None))
        pred.add(Quad(NamedNode(predicate), NamedNode(SEMSD.hasSource), NamedNode(source), None))
        pred.add(Quad(NamedNode(class_), NamedNode(SEMSD.hasProperty), NamedNode(predicate), None))
    else:
        pred.add((URIRef(predicate), RDF.type, RDF.Property))
        pred.add((URIRef(predicate), SEMSD.hasSource, URIRef(source)))
        pred.add((URIRef(class_), SEMSD.hasProperty, URIRef(predicate)))
    return pred

def _triples_predicate_range(predicate, domain, range_, source, is_pyoxigraph=False):
    predicate_range = set()
    if is_pyoxigraph:
        range_info = BlankNode()
        predicate_range.add(Quad(NamedNode(predicate), NamedNode(SEMSD.propertyRange), range_info, None))
        predicate_range.add(Quad(range_info, NamedNode(RDF.type), NamedNode(SEMSD.PropertyRange), None))
        predicate_range.add(Quad(range_info, NamedNode(RDFS.domain), NamedNode(domain), None))
        predicate_range.add(Quad(range_info, NamedNode(RDFS.range), NamedNode(range_), None))
        predicate_range.add(Quad(range_info, NamedNode(SEMSD.hasSource), NamedNode(source), None))
    else:
        range_info = BNode()
        predicate_range.add((URIRef(predicate), SEMSD.propertyRange, range_info))
        predicate_range.add((range_info, RDF.type, SEMSD.PropertyRange))
        predicate_range.add((range_info, RDFS.domain, URIRef(domain)))
        predicate_range.add((range_info, RDFS.range, URIRef(range_)))
        predicate_range.add((range_info, SEMSD.hasSource, URIRef(source)))
    return predicate_range
