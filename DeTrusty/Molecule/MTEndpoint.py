__author__ = 'Philipp D. Rohde'

import abc
from queue import Queue

from pyoxigraph import QuerySolutions as oxi_query_solution
from pyoxigraph import Store, RdfFormat
from pyoxigraph import serialize as oxi_serialize

from DeTrusty.Logger import get_logger
from DeTrusty.Molecule import SEMSD, QUERY_DELETE_PROPERTY_RANGE, QUERY_DELETE_SOURCE_FROM_PROPERTY, \
    QUERY_DELETE_PROPERTY_NO_SOURCE, QUERY_DELETE_SOURCE_FROM_CLASS, QUERY_DELETE_CLASS_NO_SOURCE, QUERY_DELETE_SOURCE
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)


class QuerySolution(object):
    def __init__(self, solution_set, cardinality: int = None):
        self.solution_set = solution_set
        self.cardinality = cardinality
        if isinstance(self.solution_set, oxi_query_solution):
            self.is_pyoxigraph = True
        else:
            self.is_pyoxigraph = False

    def __iter__(self):
        if self.is_pyoxigraph:
            for item in self.solution_set:
                res = {}
                for var in self.solution_set.variables:
                    if item[var] is None:
                        res[var.value] = None
                    else:
                        res[var.value] = item[var].value
                yield res
        else:
            r = self.solution_set.get()
            while r != 'EOF':
                res = {}
                for key, value in r.items():
                    res[key] = value['value']
                yield res
                r = self.solution_set.get()


class MTEndpoint(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def query(self, query_str):
        pass


class SPARQLEndpoint(MTEndpoint):
    def __init__(self, endpoint_url):
        self.endpoint_url = endpoint_url

    def query(self, query_str):
        res_queue = Queue()
        _, card = contact_source(self.endpoint_url, query_str, res_queue, config=None)
        return QuerySolution(res_queue, cardinality=card)


class PyOxigraphEndpoint(MTEndpoint):
    def __init__(self, ttl):
        self.ttl = Store()
        self.ttl.load(ttl, RdfFormat.TURTLE)
        self.ttl.optimize()

    def query(self, query_str):
        return QuerySolution(self.ttl.query(query_str))

    def serialize(self, path):
        oxi_serialize(self.ttl, path,
                      format=RdfFormat.TURTLE,
                      prefixes={'semsd': SEMSD})

    def delete_endpoint(self, endpoint: str):
        self.ttl.update(QUERY_DELETE_PROPERTY_RANGE.format(url=endpoint))
        self.ttl.update(QUERY_DELETE_SOURCE_FROM_PROPERTY.format(url=endpoint))
        self.ttl.update(QUERY_DELETE_PROPERTY_NO_SOURCE)
        self.ttl.update(QUERY_DELETE_SOURCE_FROM_CLASS.format(url=endpoint))
        self.ttl.update(QUERY_DELETE_CLASS_NO_SOURCE)
        self.ttl.update(QUERY_DELETE_SOURCE.format(url=endpoint))
        self.ttl.optimize()

    def add_endpoint(self, endpoint: str):
        from DeTrusty.Molecule.MTCreation import Endpoint, get_rdfmts_from_endpoint, _accessible_endpoints
        endpoint = Endpoint(endpoint, is_pyoxigraph=True)
        accessible = endpoint in _accessible_endpoints([endpoint])
        if accessible:
            endpoint_desc = get_rdfmts_from_endpoint(endpoint)
            [self.ttl.add(triple) for triple in endpoint.triples]
            [self.ttl.add(triple) for triple in endpoint_desc]
            self.ttl.optimize()
        else:
            logger.warning('{kg} is not accessible and, hence, cannot be added to the federation.'.format(kg=endpoint.url))
