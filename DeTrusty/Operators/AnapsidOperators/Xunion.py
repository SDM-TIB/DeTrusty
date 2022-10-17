"""
Created on Jul 10, 2011

Implements the Xunion operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe

Modified 2022-10-17 by Philipp D. Rohde to speed up merging both input queues.
"""

from multiprocessing import Queue, Process
from queue import Empty
from DeTrusty.Operators.Union import _Union


class Xunion(_Union):

    def __init__(self, vars_left, vars_right):
        self.left = Queue()
        self.right = Queue()
        self.qresults = Queue()
        self.vars_left = vars_left
        self.vars_right = vars_right

    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
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
        if self.vars_left == self.vars_right:
            self.same_variables()
        else:
            self.different_variables()

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    @staticmethod
    def __insert_result(in_, out, vars=None):
        # Puts the results from one input queue to the output queue.
        try:
            tuple_ = in_.get()
            while tuple_ != 'EOF':
                if vars is not None:
                    res = {}
                    res.update(vars)
                    res.update(tuple_)
                else:
                    res = tuple_
                out.put(res)
                tuple_ = in_.get()
        except Empty:
            pass

    def same_variables(self):
        # Executes the Xunion operator when the variables are the same.
        p_left = Process(target=self.__insert_result, args=(self.left, self.qresults))
        p_left.start()

        p_right = Process(target=self.__insert_result, args=(self.right, self.qresults))
        p_right.start()

        p_left.join()
        p_right.join()

    def different_variables(self):
        # Executes the Xunion operator when the variables are not the same.
        # Initialize empty tuples.
        v1 = {}
        v2 = {}

        # Add empty values to variables of the other argument.
        for v in self.vars_right:
            v1.update({v: ''})

        for v in self.vars_left:
            v2.update({v: ''})

        p_left = Process(target=self.__insert_result, args=(self.left, self.qresults, v1))
        p_left.start()

        p_right = Process(target=self.__insert_result, args=(self.right, self.qresults, v2))
        p_right.start()

        p_left.join()
        p_right.join()
