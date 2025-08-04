__author__ = 'Philipp D. Rohde'

import abc
from http import HTTPStatus
from queue import Queue

import requests
from pyoxigraph import QuerySolutions as OxiQuerySolution
from pyoxigraph import Store, RdfFormat
from pyoxigraph import serialize as oxi_serialize
from requests.auth import HTTPDigestAuth

from DeTrusty.Logger import get_logger
from DeTrusty.Molecule import SEMSD
from DeTrusty.Wrapper.RDFWrapper import contact_source

logger = get_logger(__name__)


class QuerySolution(object):
    """This class represents a query solution mapping and wraps Oxigraph and SPARQL JSON query results."""

    def __init__(self, solution_set, cardinality: int = None):
        """Initializes the QuerySolution object.

        Parameters
        ----------
        solution_set : OxiQuerySolution | Queue
            The query solution mapping to wrap.
        cardinality : int, optional
            The number of query results in the solution mapping.

        """
        self.solution_set = solution_set
        self.cardinality = cardinality
        if isinstance(self.solution_set, OxiQuerySolution):
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
    """An abstract class representing the RDF graph containing the source descriptions.

    The actual RDF graph may be implemented as a Pyoxigraph graph or a Virtuoso SPARQL endpoint.

    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def query(self, query_str):
        """Executes the given query and returns the result.

        Parameters
        ----------
        query_str : str
            The query to be executed.

        Returns
        -------
        QuerySolution
            The query solution mapping.

        """
        pass

    @staticmethod
    def _credentials2dict(username: str = None, password: str = None, keycloak: str = None):
        """Utility function to convert the credentials of an endpoint to a dictionary.

        Parameters
        ----------
        username : str, optional
            The username required to authenticate.
        password : str, optional
            The password required to authenticate.
        keycloak : str, optional
            The URL of the token server providing the access tokens.

        Returns
        -------
        dict
            The dictionary containing the credentials of the endpoint.

        """
        credentials = {}
        if username is not None:
            credentials['username'] = username
        if password is not None:
            credentials['password'] = password
        if keycloak is not None:
            credentials['keycloak'] = keycloak
        return credentials

    @abc.abstractmethod
    def add_endpoint(self, endpoint: str, username: str = None, password: str = None, keycloak: str = None):
        """Adds an endpoint to the federation.

        Parameters
        ----------
        endpoint : str
            The URL of the SPARQL endpoint to add to the federation.
        username : str, optional
            The username required to access the endpoint, the default is None.
        password : str, optional
            The password required to access the endpoint, the default is None.
        keycloak : str, optional
            The URL of the token server providing access tokens, the default is None.

        """
        pass

    @abc.abstractmethod
    def delete_endpoint(self, endpoint: str):
        """Deletes an endpoint from the federation.

        Parameters
        ----------
        endpoint : str
            The URL of the SPARQL endpoint to be removed from the federation.

        """
        pass

    @staticmethod
    def get_query_delete_property_range(endpoint_url: str):
        """Gets the query for deleting the property ranges associated with the given SPARQL endpoint.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Parameters
        ----------
        endpoint_url : str
            The URL of the SPARQL endpoint for which the information should be deleted.

        Returns
        -------
        str
            The query for deleting the property ranges associated with the given SPARQL endpoint.

        """
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

    @staticmethod
    def get_query_delete_source_from_property(endpoint_url: str):
        """Gets the query for deleting the given SPARQL endpoint as source for properties.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Parameters
        ----------
        endpoint_url : str
            The URL of the SPARQL endpoint for which the information should be deleted.

        Returns
        -------
        str
            The query for deleting the given SPARQL endpoint as source for properties.

        """
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

    @staticmethod
    def get_query_delete_property_no_source():
        """Gets the query for deleting properties with no sources.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Returns
        -------
        str
            The query for deleting properties with no sources.

        """
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

    @staticmethod
    def get_query_delete_source_from_class(endpoint_url: str):
        """Gets the query for deleting the given SPARQL endpoint as source for classes.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Parameters
        ----------
        endpoint_url : str
            The URL of the SPARQL endpoint for which the information should be deleted.

        Returns
        -------
        str
            The query for deleting the given SPARQL endpoint as source for classes.

        """
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

    @staticmethod
    def get_query_delete_class_no_source():
        """Gets the query for deleting classes with no sources.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Returns
        -------
        str
            The query for deleting classes with no sources.

        """
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

    @staticmethod
    def get_query_delete_source(endpoint_url: str):
        """Gets the query for deleting the given SPARQL endpoint.

        This query is then executed against the RDF graph containing the source descriptions
        as part of the deletion process of the given SPARQL endpoint.

        Parameters
        ----------
        endpoint_url : str
            The URL of the SPARQL endpoint for which the information should be deleted.

        Returns
        -------
        str
            The query for deleting the given SPARQL endpoint.

        """
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


class SPARQLEndpoint(MTEndpoint):
    """A class representing the RDF graph containing the source descriptions implemented as a Virtuoso SPARQL endpoint."""

    def __init__(self, endpoint_url, update_endpoint_url=None, username=None, password=None):
        """Initializes the SPARQLEndpoint object.

        Parameters
        ----------
        endpoint_url : str
            The URL of the SPARQL endpoint containing the source descriptions.
        update_endpoint_url : str, optional
            The URL of the Virtuoso endpoint for UPDATE queries, the default is None.
        username : str, optional
            The username for the Virtuoso UPDATE endpoint, default is None.
        password : str, optional
            The password for the Virtuoso UPDATE endpoint, default is None.

        """
        self.endpoint_url = endpoint_url
        self.update_endpoint_url = update_endpoint_url
        self.username = username
        self.password = password

    @property
    def default_graph(self):
        """The default graph URI required for adding and deleting data in Virtuoso."""
        return SEMSD + 'defaultGraph'

    def set_update_credentials(self, update_endpoint_url, username, password):
        """Sets the credentials for updating the source descriptions in Virtuoso.

        Parameters
        ----------
        update_endpoint_url : str
            The URL of the Virtuoso endpoint for UPDATE queries.
        username : str
            The username required to authenticate for UPDATE queries.
        password : str
            The password required to authenticate for UPDATE queries.

        """
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
            """Utility function to convert RDF triples from tuples to strings.

            Parameters
            ----------
            triples_ : list
                The list of RDF triples as tuples to convert.

            Returns
            -------
            list
                The list of RDF triples as strings.

            """
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

    def add_endpoint(self, endpoint: str, username: str = None, password: str = None, keycloak: str = None):
        from DeTrusty.Molecule.MTCreation import Endpoint, get_rdfmts_from_endpoint, _accessible_endpoints
        endpoint = Endpoint(endpoint, params=self._credentials2dict(username, password, keycloak))
        accessible = endpoint in _accessible_endpoints([endpoint])
        if accessible:
            endpoint_desc = get_rdfmts_from_endpoint(endpoint)
            self._add_triples(list(endpoint.triples))
            self._add_triples(list(endpoint_desc))
        else:
            logger.warning('{kg} is not accessible and, hence, cannot be added to the federation.'.format(kg=endpoint.url))

    def delete_endpoint(self, endpoint: str):
        self._update(self.get_query_delete_property_range(endpoint))
        self._update(self.get_query_delete_source_from_property(endpoint))
        self._update(self.get_query_delete_property_no_source())
        self._update(self.get_query_delete_source_from_class(endpoint))
        self._update(self.get_query_delete_class_no_source())
        self._update(self.get_query_delete_source(endpoint))


class PyOxigraphEndpoint(MTEndpoint):
    """A class representing the RDF graph containing the source descriptions implemented as a Pyoxigraph graph."""

    def __init__(self, ttl):
        """Initializes the PyOxigraphEndpoint object.

        Parameters
        ----------
        ttl : str
            The source descriptions to load into the Pyoxigraph graph represented in RDF as a string.

        """
        self.ttl = Store()
        self.ttl.load(ttl, RdfFormat.TURTLE)
        self.ttl.optimize()

    def query(self, query_str):
        return QuerySolution(self.ttl.query(query_str))

    def serialize(self, path):
        """Saves the source descriptions to a file.

        This method makes use of the serialization method provided by Pyoxigraph.

        Parameters
        ----------
        path : str
            The path where to save the source descriptions.

        """
        oxi_serialize(self.ttl, path,
                      format=RdfFormat.TURTLE,
                      prefixes={'semsd': SEMSD})

    def delete_endpoint(self, endpoint: str):
        self.ttl.update(self.get_query_delete_property_range(endpoint))
        self.ttl.update(self.get_query_delete_source_from_property(endpoint))
        self.ttl.update(self.get_query_delete_property_no_source())
        self.ttl.update(self.get_query_delete_source_from_class(endpoint))
        self.ttl.update(self.get_query_delete_class_no_source())
        self.ttl.update(self.get_query_delete_source(endpoint))
        self.ttl.optimize()

    def add_endpoint(self, endpoint: str, username: str = None, password: str = None, keycloak: str = None):
        from DeTrusty.Molecule.MTCreation import Endpoint, get_rdfmts_from_endpoint, _accessible_endpoints
        endpoint = Endpoint(endpoint, params=self._credentials2dict(username, password, keycloak), is_pyoxigraph=True)
        accessible = endpoint in _accessible_endpoints([endpoint])
        if accessible:
            endpoint_desc = get_rdfmts_from_endpoint(endpoint)
            [self.ttl.add(triple) for triple in endpoint.triples]
            [self.ttl.add(triple) for triple in endpoint_desc]
            self.ttl.optimize()
        else:
            logger.warning('{kg} is not accessible and, hence, cannot be added to the federation.'.format(kg=endpoint.url))
