#!/usr/bin/env python3

import getopt, sys
from pprint import pprint
import json
import logging
import urllib.parse as urlparse
from http import HTTPStatus
import requests
from multiprocessing import Queue, Process


xsd = "http://www.w3.org/2001/XMLSchema#"
owl = ""
rdf = ""
rdfs = "http://www.w3.org/2000/01/rdf-schema#"


metas = ['http://www.w3.org/ns/sparql-service-description',
         'http://www.openlinksw.com/schemas/virtrdf#',
         'http://www.w3.org/2000/01/rdf-schema#',
         'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
         'http://purl.org/dc/terms/Dataset',
         'http://bio2rdf.org/dataset_vocabulary:Endpoint',
         'http://www.w3.org/2002/07/owl#',
         "http://purl.org/goodrelations/",
         # 'http://www.ontologydesignpatterns.org/ont/',
         # 'http://www.wikidata.org',
         # 'http://schema.org',
         # 'http://xmlns.com/foaf/0.1',
         # 'http://purl.org/',
         'http://persistence.uni-leipzig.org',
         # 'http://dbpedia.org/ontology/Wikidata:',
         # 'http://dbpedia.org/class/yago/',
         "http://rdfs.org/ns/void#",
         'http://www.w3.org/ns/dcat',
         'http://www.w3.org/2001/vcard-rdf/',
         'http://www.ebusiness-unibw.org/ontologies/eclass',
         "http://bio2rdf.org/bio2rdf.dataset_vocabulary:Dataset",
         'http://www4.wiwiss.fu-berlin.de/bizer/bsbm/v01/instances/',
         'nodeID://']


logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger("rdfmts")
logger.setLevel(logging.INFO)
fileHandler = logging.FileHandler("{0}/{1}.log".format('.', 'mulder-rdfmts-log'))
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)


def contactRDFSource(query, endpoint, format="application/sparql-results+json"):
    if 'https' in endpoint:
        server = endpoint.split("https://")[1]
    else:
        server = endpoint.split("http://")[1]

    (server, path) = server.split("/", 1)
    # Formats of the response.
    json = format
    # Build the query and header.
    params = urlparse.urlencode({'query': query, 'format': json, 'timeout': 10000000})
    headers = {"Accept": "*/*", "Referer": endpoint, "Host": server}

    try:
        resp = requests.get(endpoint, params=params, headers=headers)
        if resp.status_code == HTTPStatus.OK:
            res = resp.text
            reslist = []
            if format != "application/sparql-results+json":
                return res

            try:
                res = res.replace("false", "False")
                res = res.replace("true", "True")
                res = eval(res)
            except Exception as ex:
                logger.info("EX processing res", ex)

            if type(res) is dict:
                if "results" in res:
                    for x in res['results']['bindings']:
                        for key, props in x.items():
                            # Handle typed-literals and language tags
                            suffix = ''
                            if props['type'] == 'typed-literal':
                                if isinstance(props['datatype'], bytes):
                                    suffix = '' # "^^<" + props['datatype'].decode('utf-8') + ">"
                                else:
                                    suffix = '' # "^^<" + props['datatype'] + ">"
                            elif "xml:lang" in props:
                                suffix = '' # '@' + props['xml:lang']
                            try:
                                if isinstance(props['value'], bytes):
                                    x[key] = props['value'].decode('utf-8') + suffix
                                else:
                                    x[key] = props['value'] + suffix
                            except:
                                x[key] = props['value'] + suffix

                            if isinstance(x[key], bytes):
                                x[key] = x[key].decode('utf-8')
                        reslist.append(x)
                    # reslist = res['results']['bindings']
                    return reslist, len(reslist)
                else:

                    return res['boolean'], 1

        else:
            print("Endpoint->", endpoint, resp.reason, resp.status_code, resp.text, query)
            logger.info("Endpoint->" + endpoint + str(resp.reason) + str(resp.status_code) + str(resp.text) + query)

    except Exception as e:
        # print("Exception during query execution to", endpoint, ': ', e)
        logger.info("Exception during query execution to", endpoint, ': ', e)
    finally:
        pass

    return None, -2


def get_typed_concepts(endpoint, tq, limit=-1, types=[]):
    """
    Entry point for extracting RDF-MTs of an endpoint.
    Extracts list of rdf:Class concepts and predicates of an endpoint
    :param endpoint:
    :param limit:
    :return:
    """
    referer = endpoint
    reslist = []
    if len(types) == 0:
        query = "SELECT DISTINCT ?t  WHERE{  ?s a ?t.   }"
        if limit == -1:
            limit = 100
            offset = 0
            numrequ = 0
            while True:
                query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
                res, card = contactRDFSource(query_copy, referer)
                numrequ += 1
                if card == -2:
                    limit = limit // 2
                    limit = int(limit)
                    if limit < 1:
                        break
                    continue
                if card > 0:
                    reslist.extend(res)
                if card < limit:
                    break
                offset += limit
                # time.sleep(5)
        else:
            reslist, card = contactRDFSource(query, referer)

        toremove = []
        # [toremove.append(r) for v in metas for r in reslist if v in r['t']]
        for r in reslist:
            for m in metas:
                if m in str(r['t']):
                    toremove.append(r)

        for r in toremove:
            reslist.remove(r)
    else:
        reslist = [{'t': t} for t in types]

    logger.info(endpoint)
    pprint(reslist)

    molecules = []
    for r in reslist:
        t = r['t']
        if "^^" in t:
            continue
        print(t)
        print("---------------------------------------")
        logger.info(t)

        rdfpropteries = []
        # Get predicates of the molecule t
        preds = get_predicates(referer, t)
        predicates = []
        linkedto = []
        for p in preds:
            pred = p['p']
            predicates.append(pred)

            # Get range of this predicate from this RDF-MT t
            if 'wikiPageWikiLink' not in pred:
                ranges = get_rdfs_ranges(referer, pred)
                if len(ranges) == 0:
                    rr = find_instance_range(referer, t, pred)
                    mtranges = list(set(ranges + rr))
                else:
                    mtranges = ranges
                ranges = []

                for mr in mtranges:
                    if '^^' in mr:
                        continue
                    if xsd not in mr:
                        ranges.append(mr)

                if len(ranges) > 0:
                    linkedto.extend(ranges)
                rdfpropteries.append({
                    "predicate": pred,
                    "range": ranges,
                    "policies": [
                        {
                            "dataset": endpoint,
                            "operator": "PR"
                        }
                    ]
                })

        rdfmt = {
            "rootType": t,
            "predicates": rdfpropteries,
            "linkedTo": linkedto,
            "wrappers": [{
                'url': endpoint,
                'predicates': predicates,
                "urlparam": "",
                "wrapperType": "SPARQLEndpoint"

            }]
        }
        molecules.append(rdfmt)

    logger.info("=================================")
    tq.put(molecules)
    tq.put("EOF")

    return molecules


def get_rdfs_ranges(referer, p, limit=-1):
    RDFS_RANGES = " SELECT DISTINCT ?range" \
                  "  WHERE{ <" + p + "> <http://www.w3.org/2000/01/rdf-schema#range> ?range. " \
                                     "} "
    #
    # " " \

    reslist = []
    if limit == -1:
        limit = 1000
        offset = 0
        numrequ = 0
        while True:
            query_copy = RDFS_RANGES + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            res, card = contactRDFSource(query_copy, referer)
            numrequ += 1
            if card == -2:
                limit = limit // 2
                limit = int(limit)
                # print "setting limit to: ", limit
                if limit < 1:
                    break
                continue
            if card > 1:
                reslist.extend(res)
            if card < limit:
                break
            offset += limit
            if offset > 1000:
                break
            # time.sleep(2)
    else:
        reslist, card = contactRDFSource(RDFS_RANGES, referer)

    ranges = []

    for r in reslist:
        skip = False
        for m in metas:
            if m in r['range']:
                skip = True
                break
        if not skip:
            ranges.append(r['range'])

    return ranges


def find_instance_range(referer, t, p, limit=-1):
    INSTANCE_RANGES = " SELECT DISTINCT ?r WHERE{ ?s a <" + t + ">. " \
                        " ?s <" + p + "> ?pt. " \
                        " ?pt a ?r . } "
    #
    #
    reslist = []
    if limit == -1:
        limit = 200
        offset = 0
        numrequ = 0
        while True:
            query_copy = INSTANCE_RANGES + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            res, card = contactRDFSource(query_copy, referer)
            numrequ += 1
            if card == -2:
                limit = limit // 2
                limit = int(limit)
                # print "setting limit to: ", limit
                if limit < 1:
                    break
                continue
            if card > 0:
                reslist.extend(res)
            if card < limit:
                break
            offset += limit
            if offset > 10000:
                break
            # time.sleep(2)
    else:
        reslist, card = contactRDFSource(INSTANCE_RANGES, referer)

    ranges = []

    for r in reslist:
        skip = False
        for m in metas:
            if m in r['r']:
                skip = True
                break
        if not skip:
            ranges.append(r['r'])

    return ranges


def get_predicates(referer, t, limit=-1):
    """
    Get list of predicates of a class t

    :param referer: endpoint
    :param server: server address of an endpoint
    :param path:  path in an endpoint (after server url)
    :param t: RDF class Concept extracted from an endpoint
    :param limit:
    :return:
    """
    #
    query = " SELECT DISTINCT ?p WHERE{ ?s a <" + t + ">. ?s ?p ?pt.  } "
    reslist = []
    if limit == -1:
        limit = 50
        offset = 0
        numrequ = 0
        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            res, card = contactRDFSource(query_copy, referer)
            numrequ += 1
            # print "predicates card:", card
            if card == -2:
                limit = limit // 2
                limit = int(limit)
                # print "setting limit to: ", limit
                if limit < 1:
                    print("giving up on " + query)
                    print("trying instances .....")
                    rand_inst_res = get_preds_of_random_instances(referer, t)
                    existingpreds = [r['p'] for r in reslist]
                    for r in rand_inst_res:
                        if r not in existingpreds:
                            reslist.append({'p': r})
                    break
                continue
            if card > 0:
                reslist.extend(res)
            if card < limit:
                break
            offset += limit
            # time.sleep(2)
    else:
        reslist, card = contactRDFSource(query, referer)

    return reslist


def get_preds_of_random_instances(referer, t, limit=-1):
    """
    get a union of predicated from 'randomly' selected 10 entities from the first 100 subjects returned

    :param referer: endpoint
    :param server:  server name
    :param path: path
    :param t: rdf class concept of and endpoint
    :param limit:
    :return:
    """
    query = " SELECT DISTINCT ?s WHERE{ ?s a <" + t + ">. } "
    reslist = []
    if limit == -1:
        limit = 50
        offset = 0
        numrequ = 0
        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            res, card = contactRDFSource(query_copy, referer)
            numrequ += 1
            # print "rand predicates card:", card
            if card == -2:
                limit = limit // 2
                limit = int(limit)
                # print "setting limit to: ", limit
                if limit < 1:
                    break
                continue
            if numrequ == 100:
                break
            if card > 0:
                import random
                rand = random.randint(0, card - 1)
                inst = res[rand]
                inst_res = get_preds_of_instance(referer, inst['s'])
                inst_res = [r['p'] for r in inst_res]
                reslist.extend(inst_res)
                reslist = list(set(reslist))
            if card < limit:
                break
            offset += limit
            # time.sleep(5)
    else:
        reslist, card = contactRDFSource(query, referer)

    return reslist


def get_preds_of_instance(referer, inst, limit=-1):
    query = " SELECT DISTINCT ?p WHERE{ <" + inst + "> ?p ?pt. } "
    reslist = []
    if limit == -1:
        limit = 1000
        offset = 0
        numrequ = 0
        while True:
            query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
            res, card = contactRDFSource(query_copy, referer)
            numrequ += 1
            # print "inst predicates card:", card
            if card == -2:
                limit = limit // 2
                limit = int(limit)
                # print "setting limit to: ", limit
                if limit < 1:
                    break
                continue
            if card > 0:
                reslist.extend(res)
            if card < limit:
                break
            offset += limit
            # time.sleep(2)
    else:
        reslist, card = contactRDFSource(query, referer)

    return reslist


def get_options(argv):
    try:
        opts, args = getopt.getopt(argv, "h:s:o:")
    except getopt.GetoptError:
        usage()
        sys.exit(1)

    '''
    Supported output formats:
        - json (default)       
    '''

    endpoints = None
#    output = 'config-output.json'
    for opt, arg in opts:
        if opt == "-h":
            usage()
            sys.exit()
        elif opt == "-s":
            endpoints = arg
#        elif opt == "-o":
#            output = arg

    if not endpoints:
        usage()
        sys.exit(1)
#    if '.json' not in output:
#        output += '.json'

    return endpoints#, output


def endpointsAccessible(endpoints):
    ask = "ASK {?s ?p ?o}"
    found = False
    for e in endpoints:
        referer = e
        val, c = contactRDFSource(ask, referer)
        if c == -2:
            print(e, '-> is not accessible. Please check if this endpoint properly started!')
            sys.exit(1)
        if val:
            found = True
        else:
            print(e, "-> is returning empty results. Hence, will not be included in the federation!")

    return found


def get_links(endpoint1, rdfmt1, endpoint2, rdfmt2, q):
    # print 'between endpoints:', endpoint1, ' --> ', endpoint2
    found = False
    for c in rdfmt1:
        for p in c['predicates']:
            reslist = get_external_links(endpoint1, c['rootType'], p['predicate'], endpoint2, rdfmt2)
            if len(reslist) > 0:
                found = True
                # reslist = [r+"@"+endpoint2 for r in reslist]
                c['linkedTo'].extend(reslist)
                c['linkedTo'] = list(set(c['linkedTo']))
                p['range'].extend(reslist)
                p['range'] = list(set(p['range']))
                # print 'external links found for ', c['rootType'], '->', p['predicate'], reslist
    if found:
        q.put(rdfmt1)
    else:
        q.put([])


def get_external_links(endpoint1, rootType, pred, endpoint2, rdfmt2):
    query = 'SELECT DISTINCT ?o  WHERE {?s a <' + rootType + '> ; <' + pred + '> ?o . FILTER (isIRI(?o))}'
    referer = endpoint1

    reslist = []
    limit = 45
    offset = 0
    numrequ = 0
    links_found = []
    # print("Checking external links: ", endpoint1, rootType, pred, ' in ', endpoint2)
    while True:
        query_copy = query + " LIMIT " + str(limit) + " OFFSET " + str(offset)
        res = []
        res, card = contactRDFSource(query_copy, referer)
        numrequ += 1
        if card == -2:
            limit = limit // 2
            if limit < 1:
                break
            continue
        if numrequ == 100:
            break
        if card > 0:
            for c in rdfmt2:
                if c['rootType'] in links_found:
                    continue
                if len(res) > 45:
                    for i in range(0, len(res), 45):
                        if i + 45 < len(res):
                            exists = link_exist(res[i:45], c['rootType'], endpoint2)
                        else:
                            exists = link_exist(res[i:], c['rootType'], endpoint2)
                        if exists:
                            reslist.append(c['rootType'])
                            links_found.append(c['rootType'])
                            print(rootType, ',', pred, '->', c['rootType'])
                else:
                    exists = link_exist(res, c['rootType'], endpoint2)
                    if exists:
                        reslist.append(c['rootType'])
                        links_found.append(c['rootType'])
                        print(rootType, ',', pred, '->', c['rootType'])
            reslist = list(set(reslist))
        if len(links_found) == len(rdfmt2):
            break
        if card < limit:
            break

        offset += limit

    # print(reslist)
    # print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
    return reslist


def link_exist(insts, c, endpoint):
    inst = [i['o'] if ' ' not in i['o'] else i['o'].replace(' ', '_') for i in insts]
    oinstances = ["?s = <" + i + "> " for i in inst]
    query = 'ASK {?s  a  <' + c + '> FILTER (' + " || ".join(oinstances) + ')}'
    referer = endpoint

    res, card = contactRDFSource(query, referer)
    if res is None:
        print('bad request on, ', c, insts)
    if card > 0:
        if res:
            print("ASK result", res, c, endpoint)
        return res

    return False


def usage():
    usage_str = ("Usage: {program} \n"
                 "-s <path/to/endpoints.txt> \n"
#                 "-o <path/to/output.json> \n"
                 "where \n"                                  
                 "\t<path/to/endpoints.txt> - path to a text file containing a list of SPARQL endpoint URLs \n")
#                 "\t<path/to/output.json> - name of output file  \n")

    print(usage_str.format(program=sys.argv[0]),)


def mergeMTs(rdfmt, rootType, dsrdfmts):
    otherrdfmt = dsrdfmts[rootType]

    dss = {d['url']: d for d in otherrdfmt['wrappers']}

    if rdfmt['wrappers'][0]['url'] not in dss:
        otherrdfmt['wrappers'].extend(rdfmt['wrappers'])
    else:
        pps = rdfmt['wrappers'][0]['predicates']
        dss[rdfmt['wrappers'][0]['url']]['predicates'].extend(pps)
        dss[rdfmt['wrappers'][0]['url']]['predicates'] = list(set(dss[rdfmt['wrappers'][0]['url']]['predicates']))
        otherrdfmt['wrappers'] = list(dss.values())

    otherpreds = {p['predicate']: p for p in otherrdfmt['predicates']}
    thispreds = {p['predicate']: p for p in rdfmt['predicates']}
    sameps = set(otherpreds.keys()).intersection(thispreds.keys())
    if len(sameps) > 0:
        for p in sameps:
            if len(thispreds[p]['range']) > 0:
                otherpreds[p]['range'].extend(thispreds[p]['range'])
                otherpreds[p]['range'] = list(set(otherpreds[p]['range']))
    preds = [otherpreds[p] for p in otherpreds]
    otherrdfmt['predicates'] = preds
    newpreds = set(list(thispreds.keys())).difference(list(otherpreds.keys()))
    otherrdfmt['predicates'].extend([thispreds[p] for p in newpreds])
    otherrdfmt['linkedTo'] = list(set(rdfmt['linkedTo'] + otherrdfmt['linkedTo']))


if __name__ == "__main__":
    endpointsfile = get_options(sys.argv[1:])
    output = "/DeTrusty/Config/rdfmts.json"
    with open(endpointsfile, 'r') as f:
        endpoints = f.readlines()
        if len(endpoints) == 0:
            print("Endpoints file should have at least one url")
            sys.exit(1)

        endpoints = [e for e in [e.strip('\n') for e in endpoints] if e]
        if not endpointsAccessible(endpoints):
            print("None of the endpoints can be accessed. Please check if you write URLs properly!")
            sys.exit(1)
    dsrdfmts = {}
    sparqlendps = {}
    eoffs = {}
    epros = []
    for url in endpoints:
        # rdfmts = get_typed_concepts(url)
        # sparqlendps[url] = rdfmts.copy()
        tq = Queue()
        eoffs[url] = tq
        p1 = Process(target=get_typed_concepts, args=(url, tq, ))
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

    eofflags = []
    epros = []
    for e1 in sparqlendps:
        for e2 in sparqlendps:
            if e1 == e2:
                continue
            q = Queue()
            eofflags.append(q)
            print("Finding inter-links between:", e1, ' and ', e2, ' .... ')
            print("==============================//=========//===============================")
            p = Process(target=get_links, args=(e1, sparqlendps[e1], e2, sparqlendps[e2], q,))
            epros.append(p)
            p.start()
            # get_links(e1, sparqlendps[e1], e2, sparqlendps[e2])

    while len(eofflags) > 0:
        for q in eofflags:
            rdfmts = q.get()
            for rdfmt in rdfmts:
                rootType = rdfmt['rootType']
                if rootType not in dsrdfmts:
                    dsrdfmts[rootType] = rdfmt
                else:
                    mergeMTs(rdfmt, rootType, dsrdfmts)
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
                mergeMTs(rdfmt, rootType, dsrdfmts)

    templates = list(dsrdfmts.values())
    json.dump(templates, open(output, 'w+'))
    pprint(templates)
    logger.info('-----DONE!-----')

    import os
    os._exit(0)
