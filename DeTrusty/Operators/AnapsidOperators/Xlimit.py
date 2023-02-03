"""
Created on Jul 10, 2011

Implements the Xlimit operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue


class Xlimit(object):

    name = "LIMIT"

    def __init__(self, vars, limit):
        self.input = Queue()
        self.qresults = Queue()
        self.vars = vars
        self.limit = int(limit)

    def execute(self, left, dummy, out, processqueue=Queue()):
        # print  "Executes the Xlimit.", self.limit
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)
        count = 0

        # LIMIT.
        while ((count < self.limit) and (tuple != "EOF")):
            self.qresults.put(tuple)
            count = count + 1
            # print "count", count
            tuple = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return
