"""
Created on Jul 10, 2011

Implements a Symmetric Hash Join (SHJ) operator.
The intermediate results are represented as queues.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from time import time
from DeTrusty.Operators.Join import Join
from .OperatorStructures import Table, Partition, Record


class SymmetricHashJoin(Join):

    def __init__(self, vars):
        self.left_table  = Table()
        self.right_table = Table()
        self.qresults    = Queue()
        self.vars        = vars

    def instantiate(self, d):
        newvars = self.vars - set(d.keys())
        return SymmetricHashJoin(newvars)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the Symmetric Hash Join.
        self.left     = left
        self.right    = right
        self.qresults = out

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Get the tuples from the queues.
        while (not(tuple1 == "EOF") or not(tuple2 == "EOF")):

            # Try to get and process tuple from left queue.
            if not(tuple1 == "EOF"):
                try:
                    tuple1 = self.left.get(False)
                    #print "Tuples in right table", len(self.right_table.partitions[0].records)
                    self.insertAndProbe(tuple1, self.left, self.left_table, self.right_table)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.left.get(False), when the queue is empty.
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    pass

            # Try to get and process tuple from right queue.
            if not(tuple2 == "EOF"):
                try:
                    tuple2 = self.right.get(False)
                    self.insertAndProbe(tuple2, self.right, self.right_table, self.left_table)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    pass

#            # Process tuples.
#            if (not(tuple1 == None) and not(tuple1 == "EOF")):
#                #print "Tuples in right table", len(self.right_table.partitions[0].records)
#                self.insertAndProbe(tuple1, self.left, self.left_table, self.right_table)
#            if (not(tuple2 == None) and not(tuple2 == "EOF")):
#                self.insertAndProbe(tuple2, self.right, self.right_table, self.left_table)
#

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def insertAndProbe(self, tuple, input, table1, table2):
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
        #count = 0
        if partition:

            # For every record in the partition, check if it is duplicated.
            # Then, check if the tuple matches for every join variable.
            # If there is a join, concatenate the tuples and produce result.

            for r in partition.records:
                #count = count + 1
                if self.isDuplicated(record, r):
                    break

                for v in var:
                    join = True
                    if record.tuple[v] != r.tuple[v]:
                        join = False
                        break

                if join:
                    res = record.tuple.copy()
                    res.update(r.tuple)
                    self.qresults.put(res)
                    #print count, res

    def isDuplicated(self, record1, record2):
        # Verify if the tuples has been already probed.
        return not record1.ats >= record2.ats
