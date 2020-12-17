"""
Created on Jul 10, 2011

Implements a XJoin operator.
The intermediate results are represented as queues.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
from queue import Empty
from tempfile import NamedTemporaryFile
from threading import Timer
from random import randint
from os import remove
from DeTrusty.Operators.Join import Join
from .OperatorStructures import Table, Partition, Record, FileDescriptor, isOverlapped


class XJoin(Join):

    def __init__(self, vars):
        self.left_table  = Table()
        self.right_table = Table()
        self.qresults    = Queue()
        self.vars        = vars
        self.timestamp   = 0

        # Second stage settings
        self.timeoutSecondStage  = 4
        self.leftSourceBlocked   = False
        self.rightSourceBlocked  = False

        # Main memory settings
        self.memorySize   = 10        # Represents the main memory size (# tuples).OLD:Represents the main memory size (in KB).
        self.memory_left  = 0
        self.memory_right = 0
        self.fileDescriptor_left = {}
        self.fileDescriptor_right = {}

    def instantiate(self, d):
        newvars = self.vars - set(d.keys())
        return XJoin(newvars)

    def execute(self, left, right, out, processqueue=Queue()):
        # Executes the XJoin.
        self.left     = left
        self.right    = right
        self.qresults = out

        # Initialize tuples.
        tuple1 = None
        tuple2 = None

        # Create alarms (timers) to stage 2.
        t1 = Timer(float("inf"), self.leftBlocked)
        t2 = Timer(float("inf"), self.rightBlocked)

        # Get the tuples from the queues.
        while (not(tuple1 == "EOF") or not(tuple2 == "EOF")):

            if (self.memory_left + self.memory_right >= self.memorySize):
                self.flushPartition()

            # Try to get and process tuple from left queue.
            if (not(tuple1 == "EOF")):
                try:
                    tuple1 = self.left.get(False)
                    self.leftSourceBlocked = False
                    self.timestamp += 1
                    t1.cancel()
                    t1 = Timer(self.timeoutSecondStage, self.leftBlocked)
                    t1.start()
                    self.stage1(tuple1, self.left, self.left_table, self.right_table)
                    self.memory_left += 1
                except Empty:
                    # Empty: in tuple1 = self.left.get(False), when the queue is empty.
                    #self.stage2()
                    pass
                except TypeError:
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    pass

            # Try to get and process tuple from right queue.
            if (not(tuple2 == "EOF")):
                try:
                    tuple2 = self.right.get(False)
                    self.rightSourceBlocked = False
                    self.timestamp += 1
                    t2.cancel()
                    t2 = Timer(self.timeoutSecondStage, self.rightBlocked)
                    t2.start()
                    self.stage1(tuple2, self.right, self.right_table, self.left_table)
                    self.memory_right += 1
                except Empty:
                    # Empty: in tuple1 = self.right.get(False), when the queue is empty.
                    #self.stage2()
                    pass
                except TypeError:
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    pass

        # Turn off alarms to stage 2.
        t1.cancel()
        t2.cancel()
        # Perform the last probes.
        self.stage3()

    def stage1(self, tuple, input, table1, table2):
        # Stage 1: While both sources are sending data.

        # Get the attribute(s) to apply hash.
        att = ''
        for var in self.vars:
            att = att + tuple[var]
        i = hash(att) % table1.size;

        # Insert record in partition.
        #record = Record(tuple, time(), 0)
        record = Record(tuple, self.timestamp, float("inf"))
        table1.insertRecord(i, record)

        # Probe the record against its partition in the other table.
        self.probe(record, table2.partitions[i], self.vars)

    def leftBlocked(self):
        self.leftSourceBlocked = True
        self.stage2()

    def rightBlocked(self):
        self.rightSourceBlocked = True
        self.stage2()

    def stage2(self):
        # Stage 2: When both sources stops sending data.
        if (self.leftSourceBlocked and self.rightSourceBlocked):
            # Timestamp of the secondStage
            probeTS = self.timestamp

        while (self.leftSourceBlocked and self.rightSourceBlocked):
            # Choose a random victim from main memory.
            i = randint(0, (self.left_table.size + self.right_table.size)-1)

            if (i < self.left_table.size):
                partition = self.left_table.partitions[i]
                file_descriptor = self.fileDescriptor_right
            else:
                i = i % self.right_table.size
                partition = self.right_table.partitions[i]
                file_descriptor = self.fileDescriptor_left

            # Check if the partition has been flushed and has records in main memory.
            if ((file_descriptor.has_key(i)) and (len(partition.records)>0)):
                dtsLast = 0

                for record in partition.records:
                    if (record.ats <= probeTS):
                        dtsLast = self.probeMainSecondaryMem(record, file_descriptor, i, probeTS)

                # Update the file descriptor.
                file_descriptor[i].timestamps.add((dtsLast, probeTS))

    def stage3(self):
        # Stage 3: When both sources sent all the data.

        # Partitions in main (left) memory are probed against partitions in secondary (right) memory.
        for i in range(self.left_table.size):
            partition = self.left_table.partitions[i]
            for record in partition.records:
                self.probeMainSecondaryMem(record, self.fileDescriptor_right, i, self.timestamp)

        # Partitions in main (right) memory are probed against partitions in secondary (left) memory.
        for i in range(self.right_table.size):
            partition = self.right_table.partitions[i]
            for record in partition.records:
                self.probeMainSecondaryMem(record, self.fileDescriptor_left, i, self.timestamp)

        # Partitions in secondary memory are probed.
        if (len(self.fileDescriptor_left) <= len(self.fileDescriptor_right)):
            self.probeSecondarySecondaryMem(self.fileDescriptor_left, self.fileDescriptor_right)
        else:
            self.probeSecondarySecondaryMem(self.fileDescriptor_right, self.fileDescriptor_left)

        # Delete files from secondary memory.
        for i in self.fileDescriptor_left:
            remove(self.fileDescriptor_left[i].file.name)

        for i in self.fileDescriptor_right:
            remove(self.fileDescriptor_right[i].file.name)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def probe(self, record, partition, var):
        # Probe a tuple if the partition is not empty.
        if partition:
            # For every record in the partition, check if it is duplicated.
            # Then, check if the tuple matches for every join variable.
            # If there is a join, concatenate the tuples and produce result.
            for r in partition.records:
#                if self.isDuplicated(record, r):
#                    break

                for v in var:
                    join = True
                    if record.tuple[v] != r.tuple[v]:
                        join = False
                        break

                if join:
                    res = record.tuple.copy()
                    res.update(r.tuple)
                    self.qresults.put(res)

    def probeMainSecondaryMem(self, record, filedescriptor2, partition, timestage2):
        # Probe a record against its corresponding partition in secondary memory.
        file2 = open(filedescriptor2[partition].file.name, 'r')
        records2 = file2.readlines()
        timestamps = filedescriptor2[partition].timestamps
        dtsLast = float("inf")

        for record2 in records2:
            (tuple2, ats2, dts2) = record2.split('|')
            tuple2 = eval(tuple2)
            ats2 = int(ats2)
            dts2 = int(dts2)
            dtsLast = dts2
            probedStage1 = False
            probedStage2 = False

            for v in self.vars:
                join = True
                if record.tuple[v] != tuple2[v]:
                    join = False
                    break

            if (join):
                # Check if the records were probed in stage 2.
                for pairTS in timestamps:
                    (dtsLast, probeTS) = pairTS
                    #if (isOverlapped((record.ats, record.dts), pairTS) and (record.dts >= pairTS[0])):
                    #if ((record.dts <= probeTS) and (dts2 > probeTS) and (ats2 <= probeTS)):
                    if ((dts2 <= probeTS) and (record.dts > probeTS) and (record.ats <= probeTS)):
                        probedStage2 = True
                        #print "Probed in stage 2:", (record.ats, record.dts), pairTS
                        break

                # Check if the records were probed in Stage 1.
                if (isOverlapped((record.ats, record.dts), (ats2, dts2))):
                    probedStage1 = True
                    #print "Probed in stage1:", (record.ats, record.dts), (ats2, dts2)

                # Produce result if records have not been produced.
                if (not(probedStage1) and not(probedStage2)):
                    res = record.tuple.copy()
                    res.update(tuple2)
                    self.qresults.put(res)
                    #if (len(res)==5): print "Produced at:", timestage2, res, (record.ats, record.dts), timestamps, (ats2,dts2)

        file2.close()
        return dtsLast

    def probeSecondarySecondaryMem(self, filedescriptor1, filedescriptor2):
        # Probe partitions in secondary memory.
        for partition in filedescriptor1.keys():
            if (filedescriptor2.has_key(partition)):
                file1 = open(filedescriptor1[partition].file.name, 'r')
                records1 = file1.readlines()
                timestamps1 = filedescriptor1[partition].timestamps

                for record1 in records1:
                    (tuple1, ats1, dts1) = record1.split('|')
                    tuple1 = eval(tuple1)
                    ats1 = int(ats1)
                    dts1 = int(dts1)
                    file2 = open(filedescriptor2[partition].file.name, 'r')
                    records2 = file2.readlines()
                    timestamps2 = filedescriptor2[partition].timestamps

                    for record2 in records2:
                        (tuple2, ats2, dts2) = record2.split('|')
                        tuple2 = eval(tuple2)
                        ats2 = int(ats2)
                        dts2 = int(dts2)

                        probedStage1 = False
                        probedStage2 = False

                        for v in self.vars:
                            join = True
                            if tuple1[v] != tuple2[v]:
                                join = False
                                break

                        if (join):
                            # Check if the records were probed in stage 2.
                            for pairTS in timestamps1:
                                (dtsLast, probeTS) = pairTS
                                # (dts1 <= dtsLast) and
                                if ((dts1 <= probeTS) and (dts2 > probeTS) and (ats2 <= probeTS)):
                                    probedStage2 = True
                                    break

                            for pairTS in timestamps2:
                                (dtsLast, probeTS) = pairTS
                                #(dts2 <= dtsLast) and
                                if ((dts2 <= probeTS) and (dts1 > probeTS) and (ats1 <= probeTS)):
                                    probedStage2 = True
                                    break

                            # Check if the records were probed in Stage 1.
                            if (isOverlapped((ats1, dts1), (ats2, dts2))):
                                probedStage1 = True

                            # Produce result if records have not been produced.
                            if (not(probedStage1) and not(probedStage2)):
                                res = tuple1.copy()
                                res.update(tuple2)
                                self.qresults.put(res)
                                #if (len(res)==5): print "Produced Sec Sec!:", res, (ats1, dts1), (ats2,dts2), timestamps1, timestamps2

                    file2.close()

                file1.close()

    def flushPartition(self):
        # Flush a Partition to secondary memory.

        # Choose a random victim from main memory, which size is not empty.
        victim_len = 0
        while (victim_len == 0):
            victim = randint(0, (self.left_table.size + self.right_table.size)-1)
            if (victim < self.left_table.size):
                victim_len = len(self.left_table.partitions[victim].records)
            else:
                victim_len = len(self.right_table.partitions[victim % self.right_table.size].records)

        if (victim < self.left_table.size):
            file_descriptor = self.fileDescriptor_left
            partition_to_flush = self.left_table.partitions[victim]
            self.memory_left = self.memory_left - len(partition_to_flush.records)
            self.left_table.partitions[victim] = Partition()

        else:
            victim = victim % self.right_table.size
            file_descriptor = self.fileDescriptor_right
            partition_to_flush = self.right_table.partitions[victim]
            self.memory_right = self.memory_right - len(partition_to_flush.records)
            self.right_table.partitions[victim] = Partition()

        # Update file descriptor
        if (file_descriptor.has_key(victim)):
            lenfile = file_descriptor[victim].size
            file = open(file_descriptor[victim].file.name, 'a')
            file_descriptor.update({victim: FileDescriptor(file, len(partition_to_flush.records) + lenfile, file_descriptor[victim].timestamps)})
        else:
            file = NamedTemporaryFile(suffix=".ht", prefix="", delete=False)
            file_descriptor.update({victim: FileDescriptor(file, len(partition_to_flush.records), set())})

        # Flush partition in file.
        for record in partition_to_flush.records:
            self.timestamp += 1
            tuple = str(record.tuple)
            ats   = str(record.ats)
            dts   = str(self.timestamp)
            #ats   = "%.40r" % (record.ats)
            #dts   = "%.40r" % (time())

            file.write(tuple + '|')
            file.write(ats + '|')
            file.write(dts + '\n')

        file.close()
