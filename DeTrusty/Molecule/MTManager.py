from __future__ import annotations

__author__ = 'Philipp D. Rohde and Kemele M. Endris'

import abc
import json
import os
import time
import warnings
from base64 import b64encode

import requests
from rdflib.namespace import RDFS, XSD

from DeTrusty.Molecule import SEMSD
from DeTrusty.Molecule.MTEndpoint import MTEndpoint, PyOxigraphEndpoint, SPARQLEndpoint
from DeTrusty.utils import is_url, is_sparql_endpoint, read_file_from_internet


def get_config(config_input: str | list[dict]):
    """Creates an object with the internal representation of the source descriptions.

    Based on the type of input, this function will create a ``Config`` object either
    from a local file, remote file, or a list of dictionaries. The source descriptions
    are later used by DeTrusty for the source selection and decomposition. The main
    usage of this function is to read stored source descriptions from a file (local or remote)
    in order to reuse them for query execution over the same federation.

    Parameters
    ----------
    config_input: str | list[dict]
        The source description to transform into the internal representation. Might be a string holding the path
        to a configuration file. The configuration file can be local or remote (accessible via GET request).
        The source description can also be a parsed JSON, i.e., a list of Python dictionaries. Each dictionary
        represents a so-called *RDF Molecule Template*.

    Returns
    -------
    Config
        The object holding the internal representation of the source descriptions. The result might be ``None``
        if there was an issue while reading the source descriptions that did not lead to an exception.

    Examples
    --------
    The example calls assume that the files ``rdftms.json`` and ``rdfmts.ttl`` are valid source description files created by DeTrusty.
    See `Creating Source Descriptions <https://sdm-tib.github.io/DeTrusty/library.html#creating-source-descriptions>`_
    for more information. Additionally, it is assumed that the used SPARQL endpoint is serving valid source descriptions.

    >>> get_config('./rdfmts.json')

    >>> get_config('./rdfmts.ttl')

    >>> get_config('http://example.com/rdfmts.json')

    >>> get_config('http://example.com/rdfmts.ttl')

    >>> get_config('http://src_desc.example.com/sparql')

    """
    if isinstance(config_input, list):
        return JSONConfig(config_input)
    else:
        if os.path.isfile(config_input):
            extension = os.path.splitext(config_input)[1]
            if extension.lower() == '.json':
                return ConfigFile(config_input)
            else:
                with open(config_input, 'r', encoding='utf8') as f:
                    config_ttl = f.read()
                return TTLConfig(config_ttl)
        elif is_url(config_input):
            if is_sparql_endpoint(config_input):
                config = SPARQLConfig(config_input)
            elif config_input.endswith('.json'):
                config = JSONConfig(read_file_from_internet(config_input, json_response=True))
                config.orig_file = config_input
            else:
                config = TTLConfig(read_file_from_internet(config_input, json_response=False))
                config.orig_file = config_input
            return config
    return Config()


class Config(object):
    def __init__(self, configfile=None, json_data=None):
        self.configfile = configfile
        self.metadata = {}
        self.predidx = {}
        self.predwrapidx = {}
        self.endpoints = {}
        if configfile is not None or json_data is not None:
            if json_data is not None:
                self.metadata = json_data
            self.metadata = self.getAll()
            if self.metadata is None:
                self.metadata = {}
            self.predidx = self.createPredicateIndex()
            self.predwrapidx = self.createPredicateWrapperIndex()
            self.endpoints = self.getEndpoints()

    @abc.abstractmethod
    def getAll(self):
        return

    def getEndpoints(self):
        endpoints = {}
        for m in self.metadata:
            wrappers = self.metadata[m]['wrappers']
            for w in wrappers:
                if w['url'] not in endpoints:
                    endpoints[w['url']] = w['urlparam']
        return endpoints

    def setEndpointToken(self, endpoint, token, valid_until):
        self.endpoints[endpoint]['token'] = token
        self.endpoints[endpoint]['valid_until'] = valid_until

    @staticmethod
    def __get_auth_token(server, username, password):
        payload = 'grant_type=client_credentials&client_id=' + username + '&client_secret=' + password
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        start = time.time()
        response = requests.request('POST', server, headers=headers, data=payload)
        if response.status_code != 200:
            raise Exception(str(response.status_code) + ': ' + response.text)
        return response.json()['access_token'], start + response.json()['expires_in']

    def get_auth(self, endpoint):
        params = self.endpoints.get(endpoint, None)
        if params is not None and 'username' in params and 'password' in params:
            if 'keycloak' in params:
                valid_token = False
                if 'token' in params and 'valid_until' in params:
                    current = time.time()
                    if params['valid_until'] > current:
                        valid_token = True

                if valid_token:
                    token = params['token']
                else:
                    token, valid_until = self.__get_auth_token(params['keycloak'], params['username'], params['password'])
                    self.setEndpointToken(endpoint, token, valid_until)
                return 'Bearer ' + token
            else:
                credentials = params['username'] + ':' + params['password']
                return 'Basic ' + b64encode(credentials.encode()).decode()
        return None

    def createPredicateIndex(self):
        pidx = {}
        for m in self.metadata:
            preds = self.metadata[m]['predicates']
            for p in preds:
                if p['predicate'] not in pidx:
                    pidx[p['predicate']] = set()
                    pidx[p['predicate']].add(m)
                else:
                    pidx[p['predicate']].add(m)

        return pidx

    def createPredicateWrapperIndex(self):
        idx = {}
        for m in self.metadata:
            wrappers = self.metadata[m]['wrappers']
            for wrapper in wrappers:
                preds = wrapper['predicates']
                for pred in preds:
                    if pred not in idx:
                        idx[pred] = set()
                        idx[pred].add(wrapper['url'])
                    else:
                        idx[pred].add(wrapper['url'])
        return idx

    def get_molecules(self):
        return list(self.metadata.keys())

    def get_molecule_predicates(self, mol):
        return [p['predicate'] for p in self.metadata[mol]['predicates']]

    def get_molecule_links(self, mol):
        return self.metadata[mol]['linkedTo']

    def get_molecule_links_of_pred(self, mol, pred):
        return [p['range'] for p in self.metadata[mol]['predicates'] if p['predicate'] == pred]

    def get_molecule_endpoints(self, mol):
        return [w['url'] for w in self.metadata[mol]['wrappers']]

    def get_molecule_endpoint_preds(self, mol, endpoint):
        for e in self.metadata[mol]['wrappers']:
            if e['url'] == endpoint:
                return e['predicates']

    def findbypreds(self, preds):
        res = []
        for p in preds:
            if p in self.predidx:
                res.append(self.predidx[p])
        if len(res) != len(preds):
            return []
        for r in res[1:]:
            res[0] = res[0].intersection(r)

        mols = list(res[0])
        return mols

    def find_preds_per_mt(self, preds):
        res = {}
        for p in preds:
            if p in self.predidx:
                for m in self.predidx[p]:
                    res.setdefault(m, []).append(p)

        respreds = []
        for m in res:
            respreds.extend(res[m])
        if len(set(list(respreds))) != len(preds):
            return {}

        return res

    def findbypred(self, pred):
        mols = []
        for m in self.metadata:
            mps = [pm['predicate'] for pm in self.metadata[m]['predicates']]
            if pred in mps:
                mols.append(m)
        return mols

    def findMolecule(self, molecule):
        if molecule in self.metadata:
            return self.metadata[molecule]
        else:
            return None

    def saveToFile(self, path):
        with open(path, 'w', encoding='utf8') as output_file:
            json.dump([self.metadata[m] for m in self.metadata], output_file, indent=2)


class ConfigFile(Config):
    def __init__(self, configfile):
        warnings.warn(
            'ConfigFile is deprecated and will be removed in a future release.',
            DeprecationWarning, 2
        )
        self.orig_file = configfile
        if os.path.isfile(configfile):
            super().__init__(configfile=configfile)
        else:
            super().__init__()

    def __repr__(self):
        return 'ConfigFile(' + str(self.orig_file) + ')'

    def getAll(self):
        return self.read_json_file(self.configfile)

    @staticmethod
    def read_json_file(configfile):
        try:
            with open(configfile, 'r', encoding='utf8') as f:
                mts = json.load(f)

                meta = {}
                for m in mts:
                    if m['rootType'] in meta:
                        # linkedTo
                        links = meta[m['rootType']]['linkedTo']
                        links.extend(m['linkedTo'])
                        meta[m['rootType']]['linkedTo'] = list(set(links))

                        # predicates
                        preds = meta[m['rootType']]['predicates']
                        mpreds = m['predicates']
                        ps = {p['predicate']: p for p in preds}
                        for p in mpreds:
                            if p['predicate'] in ps and len(p['range']) > 0:
                                ps[p['predicate']]['range'].extend(p['range'])
                                ps[p['predicate']]['range'] = list(set(ps[p['predicate']]['range']))
                            else:
                                ps[p['predicate']] = p

                        meta[m['rootType']]['predicates'] = []
                        for p in ps:
                            meta[m['rootType']]['predicates'].append(ps[p])

                        # wrappers
                        wraps = meta[m['rootType']]['wrappers']
                        wrs = {w['url']+w['wrapperType']: w for w in wraps}
                        mwraps = m['wrappers']
                        for w in mwraps:
                            key = w['url'] + w['wrapperType']
                            if key in wrs:
                                wrs[key]['predicates'].extend(wrs['predicates'])
                                wrs[key]['predicates'] = list(set(wrs[key]['predicates']))

                        meta[m['rootType']]['wrappers'] = []
                        for w in wrs:
                            meta[m['rootType']]['wrappers'].append(wrs[w])
                    else:
                        meta[m['rootType']] = m
            f.close()
            return meta
        except Exception as e:
            print("Exception while reading molecule templates file:", e)
            return None


class MTCreationConfig(Config):
    def __init__(self):
        super().__init__()
        self.endpoints = {}

    def addEndpoint(self, url, params: dict = None):
        if url not in self.endpoints:
            self.endpoints[url] = params

    def setEndpoints(self, endpoints: list | dict):
        self.endpoints = {}
        if isinstance(endpoints, list):
            [self.addEndpoint(e) for e in endpoints]
        elif isinstance(endpoints, dict):
            [self.addEndpoint(key, value) for key, value in endpoints.items()]

    def getAll(self):
        return None


class JSONConfig(Config):
    def __init__(self, json_data):
        warnings.warn(
            'JSONFile is deprecated and will be removed in a future release.',
            DeprecationWarning, 2
        )
        super().__init__(json_data=json_data)

    def getAll(self):
        meta = {}
        for m in self.metadata:
            meta[m['rootType']] = m
        return meta


class RDFConfig(Config):
    """The base class for all configurations based on the source descriptions described in RDF."""

    src_desc: MTEndpoint
    """The endpoint object wrapping the actual RDF graph containing the source descriptions."""

    def __init__(self):
        """Initializes the RDFConfig object."""
        super().__init__()
        self.endpoints = self.getEndpoints()

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
        self.src_desc.add_endpoint(endpoint, username, password, keycloak)
        self.endpoints = self.getEndpoints()

    def delete_endpoint(self, endpoint: str):
        """Deletes an endpoint from the federation.

        Parameters
        ----------
        endpoint : str
            The URL of the SPARQL endpoint to be removed from the federation.

        """
        self.src_desc.delete_endpoint(endpoint)
        self.endpoints = self.getEndpoints()

    def getAll(self):
        return None

    def get_molecules(self):
        """Gets all RDF Molecules of the federation.

        The list of molecules is extracted from the source description RDF graph via a SPARQL query.

        Returns
        -------
        list
            A list of all the RDF Molecules in the federation.

        """
        mts = []
        query = "SELECT DISTINCT ?mt WHERE { ?mt a " + RDFS.Class.n3() + " }"
        result = self.src_desc.query(query)
        for res in result:
            mts.append(res['mt'])
        return mts

    def get_molecule_predicates(self, mol):
        """Gets the predicates for a given RDF Molecule.

        The list of predicates is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        mol : str
            The name of the RDF Molecule for which to retrieve the predicates.

        Returns
        -------
        list
            The list of predicates for the given RDF Molecule.

        """
        preds = []
        query = "SELECT DISTINCT ?pred WHERE {\n  <" + mol + "> a " + RDFS.Class.n3() + " .\n"
        query += "  <" + mol + "> " + SEMSD.hasProperty.n3() + " ?pred .\n}"
        result = self.src_desc.query(query)
        for res in result:
            preds.append(res['pred'])
        return preds

    def get_molecule_links(self, mol):
        """Gets the links for a given RDF Molecule.

        The links are extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        mol : str
            The name of the RDF Molecule for which to retrieve the links.

        Returns
        -------
        list
            The list of links for the given RDF Molecule.

        """
        links = []
        query = "SELECT DISTINCT ?link WHERE {\n  <" + mol + "> a " + RDFS.Class.n3() + " .\n"
        query += "  <" + mol + "> " + SEMSD.linkedTo.n3() + " ?link .\n}"
        result = self.src_desc.query(query)
        for res in result:
            links.append(res['link'])
        return links

    def get_molecule_links_of_pred(self, mol, pred):
        """Gets the links for a given RDF Molecule and predicate.

        The links are extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        mol : str
            The name of the RDF Molecule for which to retrieve the links.
        pred : str
            The full URI of the predicate for which to retrieve the links.

        Returns
        -------
        list
            The list of links for the given RDF Molecule and predicate.

        """
        links = []
        query = "SELECT DISTINCT ?link WHERE {\n  <" + mol + "> a " + RDFS.Class.n3() + " .\n"
        query += "  <" + mol + "> " + SEMSD.hasProperty.n3() + " <" + pred + "> .\n"
        query += "  <" + pred + "> " + SEMSD.propertyRange.n3() + " ?prange .\n"
        query += "  ?prange " + RDFS.domain.n3() + " <" + mol + "> .\n"
        query += "  ?prange " + RDFS.range.n3() + " ?link .\n"
        query += "}"
        result = self.src_desc.query(query)
        for res in result:
            links.append(res['link'])
        return links

    def get_molecule_endpoints(self, mol):
        """Get the endpoints for the given RDF Molecule.

        The list of endpoints is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        mol : str
            The name of the RDF Molecule for which to retrieve the endpoints.

        Returns
        -------
        list
            The list of endpoints (URLs) for the given RDF Molecule.

        """
        endpoints = []
        query = "SELECT DISTINCT ?url WHERE {\n  <" + mol + "> a " + RDFS.Class.n3() + " .\n"
        query += "  <" + mol + "> " + SEMSD.hasSource.n3() + " ?source .\n"
        query += "  ?source " + SEMSD.hasURL.n3() + " ?url .\n}"
        result = self.src_desc.query(query)
        for res in result:
            endpoints.append(res['url'])
        return endpoints

    def get_molecule_endpoint_preds(self, mol, endpoint):
        """Get the predicates for the given RDF Molecule and endpoint of the federation.

        The list of predicates is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        mol : str
            The name of the RDF Molecule for which to retrieve the predicates.
        endpoint : str
            The URL of the endpoints for which to retrieve the predicates.

        Returns
        -------
        list
            The list of predicates for the given RDF Molecule and endpoint.

        """
        predicates = []
        query = "SELECT DISTINCT ?pred WHERE {\n"
        query += "  <" + mol + "> a " + RDFS.Class.n3() + " .\n"
        query += "  <" + mol + "> " + SEMSD.hasProperty.n3() + " ?pred .\n"
        query += "  ?pred " + SEMSD.hasSource.n3() + " ?source .\n"
        query += "  ?source " + SEMSD.hasURL.n3() + ' "' + endpoint + '"^^' + XSD.anyURI.n3() + ' .\n'
        query += "}"
        result = self.src_desc.query(query)
        for res in result:
            predicates.append(res['pred'])
        return predicates

    def getEndpoints(self):
        """Get all endpoints and their information of the federation.

        The information of an endpoint includes the access information like username, password and token server URL.
        All information are extracted from the source description RDF graph via a SPARQL query.

        Returns
        -------
        dict
            A dictionary containing all endpoints of the federation including their information.

        """
        endpoints = {}
        query = "SELECT DISTINCT ?url ?username ?password ?tokenServer WHERE {\n  ?endpoint a " + SEMSD.DataSource.n3() + " .\n"
        query += "  ?endpoint " + SEMSD.hasURL.n3() + " ?url .\n"
        query += "  OPTIONAL { ?endpoint " + SEMSD.username.n3() + " ?username }\n"
        query += "  OPTIONAL { ?endpoint " + SEMSD.password.n3() + " ?password }\n"
        query += "  OPTIONAL { ?endpoint " + SEMSD.tokenServer.n3() + " ?tokenServer }\n}"
        result = self.src_desc.query(query)
        for res in result:
            endpoints[res['url']] = {}
            if 'username' in res.keys() and res['username'] is not None:
                endpoints[res['url']]['username'] = res['username']
            if 'password' in res.keys() and res['password'] is not None:
                endpoints[res['url']]['password'] = res['password']
            if 'tokenServer' in res.keys() and res['tokenServer'] is not None:
                endpoints[res['url']]['keycloak'] = res['tokenServer']
        return endpoints

    def findbypreds(self, preds):
        """Get all RDF Molecules that contain the given list of predicates.

        The list of RDF Molecules is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        preds : list
            The list of predicates the RDF Molecules need to contain.

        Returns
        -------
        list
            The list of RDF Molecules that contain the given predicates.

        """
        mts = []
        query = "SELECT DISTINCT ?mt WHERE {\n  ?mt a " + RDFS.Class.n3() + " .\n"
        for p in preds:
            query += "  ?mt " + SEMSD.hasProperty.n3() + " <" + p + "> .\n"
        query += "}"
        result = self.src_desc.query(query)
        for res in result:
            mts.append(res['mt'])
        return mts

    def find_preds_per_mt(self, preds):
        """Get all RDF Molecules and matching predicates that contain at least one of the given predicates.

        The information is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        preds : list
            The list of predicates from which the RDF Molecules need to contain at least one.

        Returns
        -------
        dict
            A dictionary mapping the RDF Molecules to the predicates found from the given list.

        """
        mts = {}
        query = "SELECT DISTINCT ?mt ?pred WHERE {\n  ?mt a " + RDFS.Class.n3() + " .\n"
        query += "  ?mt " + SEMSD.hasProperty.n3() + " ?pred .\n"
        if len(preds) > 0:
            query += "  VALUES ?pred { " + ' '.join(['<' + p + '>' for p in preds]) + " }\n"
        query += "}"
        result = self.src_desc.query(query)
        for res in result:
            if not res['mt'] in mts.keys():
                mts[res['mt']] = [res['pred']]
            else:
                mts[res['mt']].append(res['pred'])
        return mts

    def findbypred(self, pred):
        """Get all RDF Molecules that contain the given predicate.

        The list of RDF Molecules is extracted from the source description RDF graph via a SPARQL query.

        Parameters
        ----------
        pred : str
            The full URI of the predicate the RDF Molecules need to contain.

        Returns
        -------
        list
            The list of RDF Molecules that contain the given predicates.

        """
        mts = []
        query = "SELECT DISTINCT ?mt WHERE {\n  ?mt a " + RDFS.Class.n3() + " .\n"
        query += "  ?mt " + SEMSD.hasProperty.n3() + " <" + pred + "> .\n"
        query += "}"
        result = self.src_desc.query(query)
        for res in result:
            mts.append(res['mt'])
        return mts

class TTLConfig(RDFConfig):
    """This class uses Pyoxigraph as backend for the RDF graph containing the source descriptions."""

    src_desc: PyOxigraphEndpoint

    def __init__(self, ttl):
        """Initializes the TTLConfig class.

        Parameters
        ----------
        ttl : str
            The source descriptions in RDF as a string.

        """
        self.src_desc = PyOxigraphEndpoint(ttl)
        super().__init__()

    def saveToFile(self, path):
        """Saves the source descriptions to a file.

        This method makes use of the serialization method provided by Pyoxigraph.

        Parameters
        ----------
        path : str
            The path where to save the source descriptions.

        """
        self.src_desc.serialize(path)

class SPARQLConfig(RDFConfig):
    """This class uses Virtuoso as backend for the RDF graph containing the source descriptions."""

    src_desc: SPARQLEndpoint

    def __init__(self, url):
        """Initializes the SPARQLConfig class.

        Parameters
        ----------
        url : str
            The URL of the Virtuoso endpoint containing the source descriptions.

        """
        self.src_desc = SPARQLEndpoint(url)
        super().__init__()

    def set_update_credentials(self, update_endpoint, username, password):
        """Sets the credentials for updating the source descriptions in Virtuoso.

        Parameters
        ----------
        update_endpoint : str
            The URL of the Virtuoso endpoint for UPDATE queries.
        username : str
            The username required to authenticate for UPDATE queries.
        password : str
            The password required to authenticate for UPDATE queries.

        """
        self.src_desc.set_update_credentials(update_endpoint, username, password)
