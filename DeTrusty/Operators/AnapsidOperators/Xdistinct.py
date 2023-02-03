"""
Created on Dec 11, 2013

Implements the Xdistinct operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue


class Xdistinct(object):

    name = "DISTINCT"

    def __init__(self, vars):
        # self.input       = Queue()
        self.qresults = Queue()
        self.vars = vars
        self.bag = {}

    def execute(self, left, dummy, out, processqueue=Queue()):
        # Executes the Xdistinct.
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)

        while (not (tuple == "EOF")):
            str_tuple = str(sorted(tuple.items()))
            get = self.bag.get(str_tuple, False)

            if not (get):
                self.qresults.put(tuple)
                self.bag.update({str_tuple: True})
            tuple = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return
