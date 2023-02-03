import abc
from multiprocessing import Queue


class Join(object):
    __metaclass__ = abc.ABCMeta

    name = "JOIN"

    @abc.abstractmethod
    def execute(self, left, right, out, processqueue=Queue()):

        return

    @abc.abstractmethod
    def instantiate(self, d):

        return

    def getCardinality(self, l, r):
        c1 = l.getCardinality()
        c2 = r.getCardinality()
        jc1 = l.getJoinCardinality(self.vars)
        jc2 = r.getJoinCardinality(self.vars)
        if max(jc1, jc2) == 0:
            return 0
        else:
            return c1 * c2 * (1 / max(jc1, jc2))

    def getJoinCardinality(self, l, r, vars):
        return max(l.getJoinCardinality(vars), r.getJoinCardinality(vars))
