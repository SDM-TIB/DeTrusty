"""
Created on Jul 10, 2011

Implements the structures used by the ANAPSID Operators.

@author: Maribel Acosta Deibe
"""

# from time import time


class Record(object):
    """
    Represents a structure that is inserted into the hash table.
    It is composed by a tuple, probeTS (timestamp when the tuple was probed)
    and insertTS (timestamp when the tuple was inserted in the table).
    """

    def __init__(self, tuple, probeTS, insertTS=None, flushTS=None):
        self.tuple = tuple
        self.probeTS = probeTS
        self.insertTS = insertTS
        self.flushTS = flushTS


class RJTTail(object):
    """
    Represents the tail of a RJT.
    It is composed by a list of records and rjtprobeTS
    (timestamp when the last tuple in the RJT was probed).
    """

    def __init__(self, record, rjtProbeTS):
        self.records = [record]
        self.rjtProbeTS = rjtProbeTS
        self.flushTS = float("inf")

    def updateRecords(self, record):
        self.records.append(record)

    def setRJTProbeTS(self, rjtProbeTS):
        self.rjtProbeTS = rjtProbeTS


class FileDescriptor(object):
    """
    Represents the description of a file, that contains a RJT in sec mem.
    It is composed by the name of the file, the associated resource,
    the current size (number of tuples), and the timestamp of the last
    RJTTail that have been flushed.
    """

    def __init__(self, file, size, lastFlushTS):
        self.file = file
        self.size = size
        self.lastFlushTS = lastFlushTS
        # self.table = table

    def getSize(self):
        return self.size

#    def setSize(self, size):
#        self.size = size
#
#    def setLastFlushTS(self, lastFlushTS):
#        self.lastFlushTS = lastFlushTS
