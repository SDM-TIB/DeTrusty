"""
Created on Jul 10, 2011

Implements the Xunion operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from queue import Empty
from DeTrusty.Operators.Union import _Union


class Xunion(_Union):

    def __init__(self, vars_left, vars_right):
        self.left = Queue()
        self.right = Queue()
        self.qresults = Queue()
        self.vars_left = vars_left
        self.vars_right = vars_right
        self.count = 0

    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
        # return Xunion(newvars_left, newvars_right, self.distinct)
        return Xunion(newvars_left, newvars_right)

    def instantiateFilter(self, instantiated_vars, filter_str):
        newvars_left = self.vars_left - set(instantiated_vars)
        newvars_right = self.vars_right - set(instantiated_vars)
        return Xunion(newvars_left, newvars_right)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the Xunion.
        self.left = left
        self.right = right
        self.qresults = out
        # print "left", hex(id(left)), "right", hex(id(right)), "out", hex(id(out))

        # Identify the kind of union to perform.
        if (self.vars_left == self.vars_right):
            self.sameVariables()
        else:
            self.differentVariables()

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def sameVariables(self):
        # Executes the Xunion operator when the variables are the same.

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Get the tuples from the queues.
        while tuple1 != "EOF" or tuple2 != "EOF":
            if tuple1 != "EOF":
                try:
                    tuple1 = self.left.get(False)
                    if tuple1 != "EOF":
                        self.count += 1
                        self.qresults.put(tuple1)
                except Empty:
                    # This catch:
                    # Empty: in tuple1 = self.left.get(False), when the queue is empty.
                    pass

            if tuple2 != "EOF":
                try:
                    tuple2 = self.right.get(False)
                    if tuple2 != "EOF":
                        self.count += 1
                        self.qresults.put(tuple2)

                except Empty:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    pass

    def differentVariables(self):
        # Executes the Xunion operator when the variables are not the same.

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Initialize empty tuples.
        v1 = {}
        v2 = {}

        # Add empty values to variables of the other argument.
        for v in self.vars_right:
            v1.update({v: ''})

        for v in self.vars_left:
            v2.update({v: ''})

        # Get the tuples from the queues.
        while (not (tuple1 == "EOF") or not (tuple2 == "EOF")):

            # Get tuple from left queue, and concatenate with empty tuple.
            if (not (tuple1 == "EOF")):
                try:
                    tuple1 = self.left.get(False)
                    if (not (tuple1 == "EOF")):
                        res = {}
                        res.update(v1)
                        res.update(tuple1)
                        self.qresults.put(res)
                        # print(tuple1)
                except Exception:
                    # This catch:
                    # Empty: in tuple1 = self.left.get(False), when the queue is empty.
                    pass

            # Get tuple from right queue, and concatenate with empty tuple.
            if (not (tuple2 == "EOF")):
                try:
                    tuple2 = self.right.get(False)
                    if (not (tuple2 == "EOF")):
                        res = {}
                        res.update(v2)
                        res.update(tuple2)
                        self.qresults.put(res)
                        # print(tuple2)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    pass
