__author__ = 'Kemele M. Endris'

import abc
import os
import json


class Config(object):
    def __init__(self, configfile):
        if os.path.isfile(configfile):
            self.configfile = configfile
            self.metadata = self.getAll()
            self.wrappers = self.getWrappers()
            self.predidx = self.createPredicateIndex()
        else:
            self.configfile = None
            self.metadata = {}
            self.wrappers = {}
            self.predidx = {}

    @abc.abstractmethod
    def getAll(self):
        return

    @abc.abstractmethod
    def getWrappers(self):
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


class ConfigFile(Config):
    def getAll(self):
        return self.readJsonFile(self.configfile)

    def getWrappers(self):
        with open(self.configfile) as f:
            conf = json.load(f)
        wrappers = {}
        if "WrappersConfig" in conf:
            if "MappingFolder" in conf['WrappersConfig']:
                self.mappingFolder = conf['WrappersConfig']['MappingFolder']

            for w in conf['WrappersConfig']:
                wrappers[w] = conf['WrappersConfig'][w]

        return wrappers

    def readJsonFile(self, configfile):
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
