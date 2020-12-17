"""
Created on Jul 10, 2011

Implements the Xproject operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue


class Xproject(object):

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
                    var = var.name[1:]
                    aux = tuple.get(var, '')
                    res.update({var: aux})
                self.qresults.put(res)
            tuple = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return
