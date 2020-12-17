"""
Created on Jul 10, 2011

Implements a Union operator.
The intermediate results are represented as lists.

@author: Maribel Acosta Deibe
"""

import itertools
from DeTrusty.Operators.Union import _Union
from multiprocessing import Queue


class Union(_Union):

    def __init__(self, vars_left, vars_right, distinct):
        self.left = []
        self.right = []
        self.results = []
        self.vars_left = set(vars_left)
        self.vars_right = set(vars_right)
        self.distinct = distinct

    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
        return Union(newvars_left, newvars_right, self.distinct)

    def execute(self, qleft, qright, out, processqueue=Queue()):
        # Executes the Union operator.
        self.left = []
        self.right = []
        self.qresults = out

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Get the tuples from the queues.
        while (not(tuple1 == "EOF") or not(tuple2 == "EOF")):
            # Try to get tuple from left queue.
            if not(tuple1 == "EOF"):
                try:
                    tuple1 = qleft.get(False)
                    if not(tuple1 == "EOF"):
                        self.left.append(tuple1)
                        #print tuple1
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.left.get(False), when the queue is empty.
                    pass

            # Try to get tuple from right queue.
            if not(tuple2 == "EOF"):
                try:
                    tuple2 = qright.get(False)
                    if not(tuple2 == "EOF"):
                        self.right.append(tuple2)
                        #print tuple2
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    pass

        if (self.vars_left == self.vars_right):
            self.sameVariables()
        else:
            self.differentVariables()
        #print "cardinalidad: "+str(len(self.results))
        # Put all the results in the output queue.
        while self.results:
            self.qresults.put(self.results.pop(0))
        #print "cardinalidad: "+str(len(self.results))

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def sameVariables(self):
        # Executes the Union operator when the variables are the same.

        # Concatenates and sort left and right lists.
        if self.distinct:
            for t in self.left:
                if not (t in self.right):
                    self.results.append(t)
            self.results.extend(self.right)
        else:
            self.results = self.left + self.right

    def differentVariables(self):
        # Executes the Union operator when the variables are not the same.

        # Iterates elements of left list.
        for tuple1 in self.left:
            res = {}
            for v in self.vars_right:
                res.update({v:''})
            res.update(tuple1)
            self.results.append(res)

        # Iterates elements of right list.
        for tuple2 in self.right:
            res = {}
            for v in self.vars_left:
                res.update({v:''})
            res.update(tuple2)
            self.results.append(res)
