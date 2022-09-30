from __future__ import annotations

__author__ = 'Kemele M. Endris and Philipp D. Rohde'

import abc
import json
import os
import time
from base64 import b64encode

import requests


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
        if os.path.isfile(configfile):
            super().__init__(configfile=configfile)
        else:
            super().__init__()

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
        super().__init__(json_data=json_data)

    def getAll(self):
        meta = {}
        for m in self.metadata:
            meta[m['rootType']] = m
        return meta
