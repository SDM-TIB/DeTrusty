"""
Created on Jul 10, 2011

Implements the Xgoptional operator.
The intermediate results are represented as queues.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from time import time
from DeTrusty.Operators.Optional import Optional
from .OperatorStructures import Record, RJTTail


class Xgoptional(Optional):

    def __init__(self, vars_left, vars_right):
        self.left_table  = dict()
        self.right_table = dict()
        self.qresults    = Queue()
        self.bag         = []
        self.vars_left   = set(vars_left)
        self.vars_right  = set(vars_right)
        self.vars        = list(self.vars_left & self.vars_right)

    def instantiate(self, d):
        newvars_left = self.vars_left - set(d.keys())
        newvars_right = self.vars_right - set(d.keys())
        return Xgoptional(newvars_left, newvars_right)

    def instantiateFilter(self, instantiated_vars, filter_str):

        newvars_left = self.vars_left - set(instantiated_vars)
        newvars_right = self.vars_right - set(instantiated_vars)
        return Xgoptional(newvars_left, newvars_right)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the Xgoptional.
        self.left     = left
        self.right    = right
        self.qresults = out

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Get the tuples from the queues.
        while (not(tuple1 == "EOF") or not(tuple2 == "EOF")):
            # Try to get and process tuple from left queue.

            if (not(tuple1 == "EOF")):

                try:
                    tuple1 = self.left.get(False)
                    if not(tuple1 == "EOF"):
                        self.bag.append(tuple1)
                    self.stage1(tuple1, self.left_table, self.right_table, self.vars_right)
                    #print  "bag after stage 1: ", self.bag
                except Exception  as e:
                    # This catch:
                 #   print "Exception ", e.message
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    # TypeError: in resource = resource + tuple[var], when the tuple is "EOF".
                    pass

            # Try to get and process tuple from right queue.
            if (not(tuple2 == "EOF")):

                try:
                    tuple2 = self.right.get(False)
                    if not(tuple2 == "EOF"):
                        self.stage1(tuple2, self.right_table, self.left_table, self.vars_left)
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    # TypeError: in resource = resource + tuple[var], when the tuple is "EOF".
                    pass

        #print " Perform the last probes."
        self.stage3()


    def stage1(self, tuple, tuple_rjttable, other_rjttable, vars):
        # Stage 1: While one of the sources is sending data.
        #print "stage 1"
        # Get the resource associated to the tuples.
        resource = ''
        for var in self.vars:
            resource = resource + tuple[var]
        #print "probe"
        # Probe the tuple against its RJT table.
        probeTS = self.probe(tuple, resource, tuple_rjttable, vars)
        #print "creating record"
        # Create the records.
        record = Record(tuple, probeTS, time())
        #print "Stage 1"
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

    #def stage2(self):
        # Stage 2: When both sources become blocked.
        #pass

    def stage2(self, signum, frame):
        # print " Stage 2: When both sources become blocked."
        self.sourcesBlocked = True

        # Get common resources.
        resources1 = set(self.left_table.keys()) & set(self.fileDescriptor_right.keys())
        resources2 = set(self.right_table.keys()) & set(self.fileDescriptor_left.keys())

        # Iterate while there are common resources and both sources are blocked.
        while ((resources1 or resources2) and self.sourcesBlocked):

            if (resources1):
                resource = resources1.pop()
                rjts1 = self.left_table[resource].records
                for rjt1 in rjts1:
                    probed = self.probeFile(rjt1, self.fileDescriptor_right, resource, 2)
                    if (probed):
                        rjt1.probeTS = time()

            elif (resources2):
                resource = resources2.pop()
                rjts1 = self.right_table[resource].records
                for rjt1 in rjts1:
                    probed = self.probeFile(rjt1, self.fileDescriptor_left, resource, 2)
                    if (probed):
                        rjt1.probeTS = time()

        # End of second stage.
        self.lastSecondStageTS = time()
        self.secondStagesTS.append(self.lastSecondStageTS)

    def stage3(self):
        # Stage 3: When both sources sent all the data.
        #print "stage 3"
        # This is the optional: Produce tuples that haven't matched already.
        #print "Length of data in xgoptional(): ", len(self.bag)
        for tuple in self.bag:
            #print 'stage 3 loop in bag'
            res_right = {}
            for var in self.vars_right:
                res_right.update({var:''})
            res = res_right
            res.update(tuple)
            self.qresults.put(res)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def probe(self, tuple, resource, rjttable, vars):
        probeTS = time()
        # If the resource is in table, produce results.
        try:
            if resource in rjttable:
                rjttable.get(resource).setRJTProbeTS(probeTS)
                list_records = rjttable[resource].records
                # Delete tuple from bag.
                try:
                    self.bag.remove(tuple)
                except ValueError:
                    pass

                for record in list_records:
                    #print "record: ", type(record.tuple), record.tuple
                    if isinstance(record.tuple, dict):
                        res = record.tuple.copy()
                        res.update(tuple)
                        self.qresults.put(res)

                        # Delete tuple from bag.
                        try:
                            self.bag.remove(record.tuple)
                        except ValueError:
                            pass
        except Exception as e:
            pass
        return probeTS
