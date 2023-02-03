import abc
from multiprocessing import Queue


class _Union(object):
    __metaclass__ = abc.ABCMeta

    name = "UNION"

    @abc.abstractmethod
    def execute(self, left, right, out, processqueue=Queue()):
        return

    @abc.abstractmethod
    def instantiate(self, d):
        return

    def getCardinality(self, l, r):
        c1 = l.getCardinality()
        c2 = r.getCardinality()
        return c1 + c2

    def getJoinCardinality(self, l, r, vars):
        return l.getJoinCardinality(vars) + r.getJoinCardinality(vars)
