__author__ = 'Philipp D. Rohde'

import abc
from http import HTTPStatus
from queue import Queue

import requests
from pyoxigraph import QuerySolutions as oxi_query_solution
from pyoxigraph import Store, RdfFormat
from pyoxigraph import serialize as oxi_serialize
from requests.auth import HTTPDigestAuth

from DeTrusty.Logger import get_logger
from DeTrusty.Molecule import SEMSD, get_query_delete_property_range, get_query_delete_source_from_property, \
    get_query_delete_property_no_source, get_query_delete_source_from_class, get_query_delete_class_no_source, \
    get_query_delete_source
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

    @abc.abstractmethod
    def add_endpoint(self, endpoint: str):
        pass

    @abc.abstractmethod
    def delete_endpoint(self, endpoint: str):
        pass


class SPARQLEndpoint(MTEndpoint):
    def __init__(self, endpoint_url, update_endpoint_url=None, username=None, password=None):
        self.endpoint_url = endpoint_url
        self.update_endpoint_url = update_endpoint_url
        self.username = username
        self.password = password

    @property
    def default_graph(self):
        return SEMSD + 'defaultGraph'

    def set_update_credentials(self, update_endpoint_url, username, password):
        self.update_endpoint_url = update_endpoint_url
        self.username = username
        self.password = password

    def query(self, query_str):
        res_queue = Queue()
        _, card = contact_source(self.endpoint_url, query_str, res_queue, config=None)
        return QuerySolution(res_queue, cardinality=card)

    def _update(self, update_query: str):
        """Updates the SPARQL endpoint using a SPARQL update query.

        The SPARQL endpoint is updated by executing the SPARQL update query.
        The server's response is analyzed in order to indicate the success of the update.

        Parameters
        ----------
        update_query : str
            The SPARQL update query that needs to be executed for the intended update.

        Returns
        -------
        bool
            A Boolean indicating the success of the update. Obviously, true
            means that the update was successful while false indicates otherwise.

        """
        if self.update_endpoint_url is None or self.username is None or self.password is None:
            logger.exception('Please provide the update endpoint and user credentials in order to update the SPARQL endpoint.')
            raise ValueError('Update endpoint and/or user credentials not set.')

        headers = {'Accept': '*/*', 'Content-type': 'application/sparql-update'}
        try:
            resp = requests.post(self.update_endpoint_url,
                                 data=update_query,
                                 headers=headers,
                                 params={'default-graph-uri': self.default_graph},
                                 auth=HTTPDigestAuth(self.username, self.password))
            if resp.status_code == HTTPStatus.OK or \
                    resp.status_code == HTTPStatus.ACCEPTED or \
                    resp.status_code == HTTPStatus.NO_CONTENT:
                return True
            else:
                print(resp.text)
                logger.error('Update ' + self.update_endpoint_url + ' returned: ' + str(resp.status_code) + '\nReason: ' +
                             str(resp.reason) + '\nFailed query:\n' + update_query)
                exit(0)
        except Exception as e:
            logger.exception('Update ' + self.update_endpoint_url + ' caused an exception: ' + str(e) +
                             '\nFailed query:\n' + update_query)

        return False

    def _add_triples(self, triples: list[tuple]):
        """Adds new data of the RDF Molecule Templates into the RDF knowledge graph.

        This method uses INSERT queries to add new data to the RDF knowledge graph
        containing the RDF Molecule Templates. Based on the length of the data,
        several requests might be sent since Virtuoso only supports 49 triples at a time.

        Parameters
        ----------
        triples : list
            A list of RDF triples to insert into the knowledge graph.

        """
        def triples2str(triples_: list[tuple]) -> list[str]:
            return [triple[0].n3() + ' ' + triple[1].n3() + ' ' + triple[2].n3() for triple in triples_]

        i = 0
        # Virtuoso supports only 49 triples at a time.
        for i in range(0, len(triples), 49):
            if i + 49 > len(triples):
                update_query = 'INSERT DATA { ' + ' . \n'.join(triples2str(triples[i:])) + '}'
            else:
                update_query = 'INSERT DATA { ' + ' . \n'.join(triples2str(triples[i:i + 49])) + '}'
            self._update(update_query)
        if i < len(triples) + 49:
            update_query = 'INSERT DATA { ' + ' . \n'.join(triples2str(triples[i:])) + '}'
            self._update(update_query)

    def add_endpoint(self, endpoint: str):
        from DeTrusty.Molecule.MTCreation import Endpoint, get_rdfmts_from_endpoint, _accessible_endpoints
        endpoint = Endpoint(endpoint)
        accessible = endpoint in _accessible_endpoints([endpoint])
        if accessible:
            endpoint_desc = get_rdfmts_from_endpoint(endpoint)
            self._add_triples(list(endpoint.triples))
            self._add_triples(list(endpoint_desc))
        else:
            logger.warning('{kg} is not accessible and, hence, cannot be added to the federation.'.format(kg=endpoint.url))

    def delete_endpoint(self, endpoint: str):
        self._update(get_query_delete_property_range(endpoint))
        self._update(get_query_delete_source_from_property(endpoint))
        self._update(get_query_delete_property_no_source())
        self._update(get_query_delete_source_from_class(endpoint))
        self._update(get_query_delete_class_no_source())
        self._update(get_query_delete_source(endpoint))


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
        self.ttl.update(get_query_delete_property_range(endpoint))
        self.ttl.update(get_query_delete_source_from_property(endpoint))
        self.ttl.update(get_query_delete_property_no_source())
        self.ttl.update(get_query_delete_source_from_class(endpoint))
        self.ttl.update(get_query_delete_class_no_source())
        self.ttl.update(get_query_delete_source(endpoint))
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
