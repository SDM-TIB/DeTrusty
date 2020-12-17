"""
Created on Jul 10, 2011

Implements the structures used by the Blocking Operators.

@author: Maribel Acosta Deibe
"""


class Record(object):
    """
    Represents a structure that is inserted into the hash table.
    It is composed by a tuple, ats (arrival timestamp) and
    dts (departure timestamp).
    """

    def __init__(self, tuple, ats, dts):
        self.tuple = tuple
        self.ats = ats
        self.dts = dts


class Partition(object):
    """
    Represents a bucket of the hash table.
    It is composed by a list of records, and a list of timestamps
    of the form {DTSlast, ProbeTS}
    """

    def __init__(self):
        self.records = []  # List of records
        self.timestamps = []  # List of the form {DTSlas, ProbeTS}


class Table(object):
    """
    Represents a hash table.
    It is composed by a list of partitions (buckets) of size n,
    where n is specified in "size".
    """

    def __init__(self):
        self.size = 3
        self.partitions = [Partition() for x in range(self.size)]

    def getSize(self):
        return self.size

    def insertRecord(self, i, value):
        self.partitions[i].records.append(value)
