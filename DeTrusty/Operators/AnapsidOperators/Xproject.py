"""
Created on Jul 10, 2011

Implements the Xproject operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from . import Xexpression
from DeTrusty.Sparql.Parser.services import Expression, Aggregate


class Xproject(object):

    name = "PROJECT"

    def __init__(self, vars):
        self.input = Queue()
        self.qresults = Queue()
        self.vars = vars

    def execute(self, left, dummy, out, processqueue=Queue()):
        # Executes the Xproject.
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)
        while not (tuple == "EOF"):
            res = {}
            if len(self.vars) == 0:
                self.qresults.put(dict(tuple))
            else:
                for var in self.vars:
                    alias = None
                    if isinstance(var, Expression) or isinstance(var, Aggregate):
                        tmp = Xexpression.simplifyExp(var, tuple)
                        tuple.update({var.alias[1:]: str(tmp)})
                        var = var.alias[1:]
                    else:
                        if var.alias is not None:
                            alias = var.alias[1:]
                        var = var.name[1:]
                    aux = tuple.get(var, '')
                    if alias is not None:
                        res.update({alias: aux})
                    else:
                        res.update({var: aux})
                self.qresults.put(res)

            tuple = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return
