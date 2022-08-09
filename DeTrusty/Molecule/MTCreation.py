__author__ = 'Philipp D. Rohde and Kemele M. Endris'

import json
import logging
import multiprocessing
import sys
from queue import Queue
from time import time
from typing import List

from DeTrusty.Logger import get_logger
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger('rdftms', './rdfmts-log.log', file_and_console=True)

DEFAULT_OUTPUT_PATH = '/DeTrusty/Config/rdfmts.json'

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
    """Simple representation of an endpoint. URL is mandatory but an endpoint might have optional parameters."""
    def __init__(self, url: str, params: dict = None):
        self.url = url
        self.params = params


def create_rdfmts(endpoints: List[Endpoint], output: str = DEFAULT_OUTPUT_PATH):
    logger_wrapper = get_logger('DeTrusty.Wrapper.RDFWrapper')
    logger_wrapper.setLevel(logging.WARNING)  # temporarily disable logging of contacting the source

    try:
        with open(output, 'a') as f:
            if not f.writable():
                raise PermissionError
    except FileNotFoundError:
        logger.critical('No such file or directory: ' + output + '\tMake sure the directories exist!')
        return
    except PermissionError:
        logger.critical('You may not have permissions to open or write to the file: ' + output +
                        '\tPlease, check your permissions!')
        return

    dsrdfmts = {}
    sparqlendps = {}
    eoffs = {}
    epros = []
    start = time()

    endpoints = _accessible_endpoints(endpoints)
    if len(endpoints) == 0:
        logger.critical('None of the endpoints can be accessed. Please check if you write URLs properly!')
        sys.exit(1)
    for e in endpoints:
        tq = multiprocessing.Queue()
        eoffs[e.url] = tq
        p1 = multiprocessing.Process(target=_collect_rdfmts_from_source, args=(e, tq,))
        epros.append(p1)
        p1.start()

    while len(eoffs) > 0:
        for url in eoffs:
            q = eoffs[url]
            rdfmts = q.get()
            sparqlendps[url] = rdfmts
            del eoffs[url]
            break
    for p in epros:
        if p.is_alive():
            p.terminate()

    # now the interlinking
    eofflags = []
    epros = []
    for e1 in endpoints:
        for e2 in endpoints:
            if e1 == e2:
                continue
            q = multiprocessing.Queue()
            eofflags.append(q)
            logger.info('Finding inter-links between: ' + e1.url + ' and ' + e2.url)
            logger.info('==============================//=========//===============================')
            p = multiprocessing.Process(target=_get_links, args=(e1, sparqlendps[e1.url], e2, sparqlendps[e2.url], q,))
            epros.append(p)
            p.start()

    while len(eofflags) > 0:
        for q in eofflags:
            rdfmts = q.get()
            for rdfmt in rdfmts:
                rootType = rdfmt['rootType']
                if rootType not in dsrdfmts:
                    dsrdfmts[rootType] = rdfmt
                else:
                    _merge_mts(rdfmt, rootType, dsrdfmts)
            eofflags.remove(q)
            break

    for p in epros:
        if p.is_alive():
            p.terminate()

    for e in sparqlendps:
        rdfmts = sparqlendps[e]
        for rdfmt in rdfmts:
            rootType = rdfmt['rootType']
            if rootType not in dsrdfmts:
                dsrdfmts[rootType] = rdfmt
            else:
                _merge_mts(rdfmt, rootType, dsrdfmts)

    templates = list(dsrdfmts.values())
    duration = time() - start
    json.dump(templates, open(output, 'w'), indent=2)
    logger.info('----- DONE in ' + str(duration) + ' seconds!-----')
    logger_wrapper.setLevel(logging.INFO)  # reset the logger


def _collect_rdfmts_from_source(endpoint: Endpoint, tq):
    # get the typed concepts, predicates, etc. for one source
    concepts = _get_typed_concepts(endpoint)
    logger.info(endpoint.url + ': ' + str(concepts))
    molecules = []
    for c in concepts:
        if '^^' in c:
            continue
        logger.info(c)
        class_properties = []
        linked_to = set()
        predicates = _get_predicates(endpoint, c)
        for p in predicates:
            range_ = _get_predicate_range(endpoint, c, p)
            if len(range_) > 0:
                [linked_to.add(r) for r in range_]
            class_properties.append({
                'predicate': p,
                'range': range_,
                'policies': [{'dataset': endpoint.url, 'operator': 'PR'}]
            })
        endpoint.params.pop('token', None)
        endpoint.params.pop('valid_until', None)
        molecules.append({
            'rootType': c,
            'predicates': class_properties,
            'linkedTo': list(linked_to),
            'wrappers': [{
                'url': endpoint.url,
                'predicates': predicates,
                'urlparam': endpoint.params,
                'wrapperType': 'SPARQLEndpoint'
            }]
        })

    logger.info('=================================')
    tq.put(molecules)
    tq.put('EOF')
    return molecules


def _get_typed_concepts(endpoint):
    query = 'SELECT DISTINCT ?t WHERE { ?s a ?t . }'
    res_list, _ = _get_results_iter(query, endpoint)
    return [r['t'] for r in res_list if True not in [m in str(r['t']) for m in metas]]


def _get_predicates(endpoint, type_):
    query = 'SELECT DISTINCT ?p WHERE { ?s a <' + type_ + '> . ?s ?p ?pt . }'
    res_list, status = _get_results_iter(query, endpoint)
    res_list = [r['p'] for r in res_list]

    if status == -1:  # fallback - get predicates from randomly selected instances of the type
        logger.warn('giving up on ' + query)
        logger.warn('trying instances...')
        rand_inst_res = _get_predicates_of_random_instances(endpoint, type_)
        for pred in rand_inst_res:
            if pred not in res_list:
                res_list.append(pred)

    return res_list


def _get_predicates_of_random_instances(endpoint, type_):
    query = 'SELECT DISTINCT ?s WHERE { ?s a <' + type_ + '> . }'
    res_list, _ = _get_results_iter(query, endpoint, limit=100, max_tries=100, max_answers=100)
    results = []
    batches = [res_list[i:i+10] for i in range(0, len(res_list), 10)]
    for batch in batches:
        batch = ['<' + r['s'] + '>' for r in batch]
        query = 'SELECT DISTINCT ?p WHERE {\n' \
                '  VALUES ?s { ' + ' '.join(batch) + ' }\n' \
                '  ?s ?p ?pt\n}'
        res_list_batch, _ = _get_results_iter(query, endpoint)
        results.extend([r['p'] for r in res_list_batch])
    return list(set(results))


def _get_predicate_range(endpoint, type_, predicate):
    # first, get the range using rdfs:range
    query = 'SELECT DISTINCT ?range WHERE { <' + predicate + '> <http://www.w3.org/2000/01/rdf-schema#range> ?range . }'
    res_list, _ = _get_results_iter(query, endpoint)
    ranges = [r['range'] for r in res_list if True not in [m in str(r['range']) for m in metas]]

    # second, get range from instances
    query = 'SELECT DISTINCT ?range WHERE {\n' \
            '  ?s a <' + type_ + '> .\n' \
            '  ?s <' + predicate + '> ?pt .\n' \
            '  ?pt a ?range .\n}'
    res_list, _ = _get_results_iter(query, endpoint)
    ranges.extend([r['range'] for r in res_list if True not in [m in str(r['range']) for m in metas]])

    return list(set(ranges))


def _accessible_endpoints(endpoints):
    ask = 'ASK { ?s ?p ?o }'
    accessible_endpoints = []
    for e in endpoints:
        url = e.url
        val, c = contact_source(url, ask, Queue(), params=e.params)
        if c == -2:
            logger.error(url + ' --> is not accessible. Please check if this endpoint properly started!')
            sys.exit(1)
        if val:
            accessible_endpoints.append(e)
        else:
            logger.info(url + ' --> is returning empty results. Hence, will not be included in the federation!')

    return accessible_endpoints


def _get_results_iter(query: str, endpoint: Endpoint, limit: int = -1, max_tries: int = -1, max_answers: int = -1):
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
        _, card = contact_source(endpoint.url, query_copy, res_queue, params=endpoint.params)

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
                res_list.append(res)
                res = res_queue.get()

        # stop if all results are retrieved or the maximum number of tries is reached
        if card < limit or (0 < max_answers <= len(res_list)) or num_requests == max_tries:
            break

        offset += limit

    return res_list, status


def _get_links(endpoint1, rdfmt1, endpoint2, rdfmt2, q):
    found = False
    for c in rdfmt1:
        for p in c['predicates']:
            if p['predicate'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
                continue
            ext_links = _get_external_links(endpoint1, c['rootType'], p['predicate'], endpoint2, rdfmt2)
            if len(ext_links) > 0:
                found = True
                c['linkedTo'].extend(ext_links)
                c['linkedTo'] = list(set(c['linkedTo']))
                p['range'].extend(ext_links)
                p['range'] = list(set(p['range']))
    if found:
        q.put(rdfmt1)
    else:
        q.put([])
    q.put('EOF')


def _get_external_links(endpoint1, root_type, predicate, endpoint2, rdfmt2):
    query = 'SELECT DISTINCT ?o WHERE { ?s a <' + root_type + '> ; <' + predicate + '> ?o . FILTER (isIRI(?o)) }'
    e1_objects, _ = _get_results_iter(query, endpoint1, max_tries=100)
    e1_objects = [obj['o'] for obj in e1_objects]
    batches = [e1_objects[i:i + 45] for i in range(0, len(e1_objects), 45)]
    linked_to = set()
    for batch in batches:
        batch = ['<' + r + '>' for r in batch]
        query = 'SELECT DISTINCT ?c WHERE {\n' \
                '  VALUES ?o { ' + ' '.join(batch) + ' }\n' \
                '  ?s ?p ?o .\n' \
                '  ?s a ?c .\n' \
                '}'
        res_list, _ = _get_results_iter(query, endpoint2, max_tries=10)
        [linked_to.add(r['c']) for r in res_list]

        if len(linked_to) == len(rdfmt2):
            break
    if len(linked_to) > 0:
        logger.info(root_type + ', ' + predicate + ' --> ' + str(linked_to))
    return list(linked_to)


def _merge_mts(rdfmt, root_type, dsrdfmts):
    otherrdfmt = dsrdfmts[root_type]

    dss = {d['url']: d for d in otherrdfmt['wrappers']}

    if rdfmt['wrappers'][0]['url'] not in dss:
        otherrdfmt['wrappers'].extend(rdfmt['wrappers'])
    else:
        pps = rdfmt['wrappers'][0]['predicates']
        dss[rdfmt['wrappers'][0]['url']]['predicates'].extend(pps)
        dss[rdfmt['wrappers'][0]['url']]['predicates'] = list(set(dss[rdfmt['wrappers'][0]['url']]['predicates']))
        otherrdfmt['wrappers'] = list(dss.values())

    predicates_other = {p['predicate']: p for p in otherrdfmt['predicates']}
    predicates_this = {p['predicate']: p for p in rdfmt['predicates']}
    predicates_same = set(predicates_other.keys()).intersection(predicates_this.keys())
    for p in predicates_same:
        if len(predicates_this[p]['range']) > 0:
            predicates_other[p]['range'].extend(predicates_this[p]['range'])
            predicates_other[p]['range'] = list(set(predicates_other[p]['range']))
    preds = [predicates_other[p] for p in predicates_other]
    otherrdfmt['predicates'] = preds
    newpreds = set(list(predicates_this.keys())).difference(list(predicates_other.keys()))
    otherrdfmt['predicates'].extend([predicates_this[p] for p in newpreds])
    otherrdfmt['linkedTo'] = list(set(rdfmt['linkedTo'] + otherrdfmt['linkedTo']))
