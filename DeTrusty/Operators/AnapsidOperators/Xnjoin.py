"""
Created on Jul 10, 2011

Implements the Xnjoin operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from time import time
from DeTrusty.Operators.Join import Join
from .OperatorStructures import Record, RJTTail


class Xnjoin(Join):

    def __init__(self, vars):
        self.left_table  = dict()
        self.right_table = dict()
        self.qresults    = Queue()
        self.vars        = vars

    def instantiate(self, d):
        newvars = self.vars - set(d.keys())
        return Xnjoin(newvars)

    def instantiateFilter(self, instantiated_vars, filter_str):
        newvars = self.vars - set(instantiated_vars)
        return Xnjoin(newvars)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the Xgjoin.
        self.left     = left
        self.right    = right
        self.qresults = out

        # Get tuples from queue.
        tuple = self.left.get(True)

        # Get the tuples from the queues.
        while (not(tuple == "EOF")):
            self.stage1(tuple, self.left_table, self.right_table)
            tuple = self.left.get(True)

        # Perform the last probes.
        self.stage3()


    def stage1(self, tuple, tuple_rjttable, other_rjttable):
        # Stage 1: While one of the sources is sending data.

        # Get the resource associated to the tuples.
        resource = ''
        for var in self.vars:
            resource = resource + tuple[var]

        # Probe the tuple against its RJT table.
        probeTS = self.probe(tuple, resource, tuple_rjttable, other_rjttable)

        # Create the records.
        record = Record(tuple, probeTS, time())

        # Insert the record in the other RJT table.
        # TODO: use RJTTail. Check ProbeTS
        if resource in other_rjttable:
            other_rjttable.get(resource).updateRecords(record)
            other_rjttable.get(resource).setRJTProbeTS(probeTS)
            #other_rjttable.get(resource).append(record)
        else:
            tail = RJTTail(record, float("inf"))
            other_rjttable[resource] = tail
            #other_rjttable[resource] = [record]

    def stage2(self):
        # Stage 2: When both sources become blocked.
        pass

    def stage3(self):
        # Stage 3: When both sources sent all the data.

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def probe(self, tuple, resource, rjttable, other_rjttable):
        probeTS = time()

        # If the resource is in table, produce results.
        if resource in rjttable:
            rjttable.get(resource).setRJTProbeTS(probeTS)
            list_records = rjttable[resource].records
            #list_records = rjttable[resource]

            for record in list_records:
                res = record.tuple.copy()
                res.update(tuple)
                self.qresults.put(res)

        # If not, contact the source.
        else:
            instances = []
            for v in self.vars:
                instances = instances + [tuple[v]]

            # Contact the source.
            qright = Queue()
            # print "instances: "+str(instances)
            self.right.execute(self.vars, instances, qright)

            # Get the tuples from right queue.
            rtuple = qright.get(True)
            while (not(rtuple == "EOF")):
                # Build answer and produce it.
                rtuple_copy = rtuple.copy()
                rtuple_copy.update(tuple)
                self.qresults.put(rtuple_copy)

                # Create and insert the record in the left RJT table.
                record = Record(rtuple, probeTS, time())
                if resource in rjttable:
                    other_rjttable.get(resource).updateRecords(record)
                    other_rjttable.get(resource).setRJTProbeTS(probeTS)
                else:
                    tail = RJTTail(record, float("inf"))
                    other_rjttable[resource] = tail

                rtuple = qright.get(True)

        return probeTS

#    def fase1(self, tuple1, tuple2):
#
#        # Get the resource associated to the tuples
#        resource1 = ''
#        resource2 = ''
#        for var in self.vars:
#            resource1 = resource1 + tuple1[var]
#            resource2 = resource2 + tuple2[var]
#
#        # Probe the tuple against its RJT table.
#        # Create the records.
#        # Insert the records in RJT tables.
#        probeTS1 = self.probe(tuple1, resource1, self.tablaizq)
#        record1 = Record(tuple1, probeTS1, time.time())
#
#        if resource1 in self.tablader:
#            self.tablader.get(resource1).append(record1)
#        else:
#            self.tablader[resource1] = [record1]
#
#        # Probe the tuple against its RJT table.
#        # Create the records.
#        # Insert the records in RJT tables.
#
#        probeTS2 = self.probe(tuple2, resource2, self.tablader)
#        record2 = Record(tuple2, probeTS2, time.time())
#        if resource2 in self.tablaizq:
#            self.tablaizq.get(resource2).append(record2)
#        else:
#            self.tablaizq[resource2] = [record2]
#        #other_rjttable.insertRecord(resource, record)
