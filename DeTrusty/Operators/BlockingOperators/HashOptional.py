"""
Created on Jul 10, 2011

Implements a Hash Optional operator.
The intermediate results are represented as a Queue, but it doesn't
work until all the tuples are arrived.

@author: Maribel Acosta Deibe
"""

from time import time
from DeTrusty.Operators.Optional import Optional
from .OperatorStructures import Table, Record
from multiprocessing import Queue


class HashOptional(Optional):

    def __init__(self, vars_left, vars_right):
        self.left_table  = Table()
        self.right_table = Table()
        self.results     = []
        self.bag         = []
        self.results     = []
        self.vars_left   = set(vars_left)
        self.vars_right  = set(vars_right)
        self.vars        = list(self.vars_left & self.vars_right)

    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
        return HashOptional(newvars_left, newvars_right)

    def execute(self, qleft, qright, out, processqueue=Queue()):
        # Executes the Hash Optional.
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
                    self.left.append(tuple1)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.left.get(False), when the queue is empty.
                    pass

            # Try to get tuple from right queue.
            if not(tuple2 == "EOF"):
                try:
                    tuple2 = qright.get(False)
                    self.right.append(tuple2)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    pass

        # Get the variables to join.
        if ((len(self.left) > 1) and (len(self.right) > 1)):
            # Iterate over the lists to get the tuples.
            while ((len(self.left) > 1) or (len(self.right) > 1)):
                if len(self.left) > 1:
                    tuple1 = self.left.pop(0)
                    self.bag.append(tuple1)
                    self.insertAndProbe(tuple1, self.left_table, self.right_table)
                if len(self.right) > 1:
                    tuple2 = self.right.pop(0)
                    self.insertAndProbe(tuple2, self.right_table, self.left_table)

        # This is the optional.
        res_right = {}
        for var in self.vars_right:
            res_right.update({var: ''})
        for tuple in self.bag:
            res = res_right
            res.update(tuple)
            self.results.append(res)

        # Put all the results in the output queue.
        while self.results:
            self.qresults.put(self.results.pop(0))

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def insertAndProbe(self, tuple, table1, table2):
        # Insert the tuple in its corresponding partition and probe.

        # Get the attribute(s) to apply hash.
        att = ''
        for var in self.vars:
            att = att + tuple[var]
        i = hash(att) % table1.size;

        # Insert record in partition.
        record = Record(tuple, time(), 0)
        table1.insertRecord(i, record)

        # Probe the record against its partition in the other table.
        self.probe(record, table2.partitions[i], self.vars)

    def probe(self, record, partition, var):
        # Probe a tuple if the partition is not empty.
        if partition:
            # For every record in the partition, check if it is duplicated.
            # Then, check if the tuple matches for every join variable.
            # If there is a join, concatenate the tuples and produce result.
            # If there is no join, concatenate the tuple with an empty tuple.
            for r in partition.records:
                if self.isDuplicated(record, r):
                    break

                for v in var:
                    join = True
                    if record.tuple[v] != r.tuple[v]:
                        join = False
                        break

                # This is the join.
                if join:
                    res = record.tuple.copy()
                    res.update(r.tuple)
                    self.results.append(res)

                    try:
                        self.bag.remove(r.tuple)
                    except ValueError:
                        pass

                    try:
                        self.bag.remove(record.tuple)
                    except ValueError:
                        pass

    def isDuplicated(self, record1, record2):
        # Verify if a two tuples has been already probed.
        return not record1.ats >= record2.ats
