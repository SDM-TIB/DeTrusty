__author__ = 'Philipp D. Rohde'

import abc
from DeTrusty.Wrapper.RDFWrapper import contact_source
from queue import Queue
from pyoxigraph import Store, RdfFormat
from pyoxigraph import QuerySolutions as oxi_query_solution


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
