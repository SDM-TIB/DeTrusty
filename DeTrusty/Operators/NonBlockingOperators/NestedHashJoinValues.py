"""
NestedHashJoinValues.py

Implements a depending operator, similar to block nested join and symmetric hash join.
The NestedHashJoinValues is based on the NestedHashJoinFilter but uses the VALUES clause instead of filters.

Autor: Philipp D. Rohde
Date: July 19th, 2024
"""

from multiprocessing import Queue
from time import time
from queue import Empty
from DeTrusty.Operators.Join import Join
from .OperatorStructures import Record
from ...Sparql.Parser.services import Bind

WINDOW_SIZE = 20


class NestedHashJoinValues(Join):

    def __init__(self, vars):
        self.left_table = dict()
        self.right_table = dict()
        self.qresults    = Queue()
        self.vars        = vars
        self.left_queue = Queue()
        self.right_operator = None
        self.qresults = Queue()

    def execute(self, left_queue, right_operator, out, processqueue=Queue()):
        print('In NHJF')
        self.left_queue = left_queue
        self.right_operator = right_operator
        self.qresults = out
        # print("right_operator", right_operator)
        tuple1 = None
        tuple2 = None
        right_queues = dict()
        filter_bag = []
        count = 0
        while not(tuple1 == "EOF") or (len(right_queues) > 0):
            try:
                tuple1 = self.left_queue.get(False)
                # Try to get and process tuple from left queue
                if not (tuple1 == "EOF"):
                    # tuple1 = self.left_queue.get(False)
                    # print("tuple1: " + str(tuple1))
                    instance = self.probeAndInsert1(tuple1, self.right_table, self.left_table, time())
                    # print("Exit probe and insert 1 with tuple", tuple1)
                    if instance:  # the join variables have not been used to
                        # instantiate the right_operator
                        filter_bag.append(tuple1)
                    # print("filter_bag", len(filter_bag))

                    if len(filter_bag) >= WINDOW_SIZE:
                        new_right_operator = self.makeInstantiation(filter_bag, self.right_operator)
                        # print("Here in makeInstantation with filter")
                        # resource = self.getResource(tuple1)
                        queue = Queue()
                        right_queues[count] = queue
                        new_right_operator.execute(queue)
                        filter_bag = []
                        count = count + 1

                else:
                    if len(filter_bag) > 0:
                        # print("here", len(filter_bag), filter_bag)
                        new_right_operator = self.makeInstantiation(filter_bag,
                                                                    self.right_operator)
                        # resource = self.getResource(tuple1)
                        queue = Queue()
                        right_queues[count] = queue
                        new_right_operator.execute(queue)
                        filter_bag = []
                        count = count + 1

            except Empty:
                pass
            except Exception as e:
                # print("Unexpected error:", sys.exc_info()[0])
                # print(e)
                pass

            toRemove = []  # stores the queues that have already received all its tuples
            # print("right_queues", right_queues)
            for r in right_queues:
                try:
                    q = right_queues[r]
                    tuple2 = None
                    while tuple2 != "EOF":
                        tuple2 = q.get(False)

                        if tuple2 == "EOF":
                            toRemove.append(r)
                        else:
                            resource = self.getResource(tuple2)
                            for v in self.vars:
                                del tuple2[v]
                            # print("new tuple2", tuple2)
                            self.probeAndInsert2(resource, tuple2, self.left_table, self.right_table, time())
                except Exception:
                    # This catch:
                    # Empty: in tuple2 = self.right.get(False), when the queue is empty.
                    # TypeError: in att = att + tuple[var], when the tuple is "EOF".
                    # print("Unexpected error:", sys.exc_info())
                    pass

            for r in toRemove:
                if r in right_queues:
                    del right_queues[r]
        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def getResource(self, tuple):
        resource = ''
        for var in self.vars:
            val = tuple[var]['value']
            if "^^<" in val:
                val = val[:val.find('^^<')]
            resource = resource + val
        return resource

    def makeInstantiation(self, filter_bag, operators):
        new_vars = ['?' + v for v in self.vars]  # TODO: this might be $
        filter_str = " . ".join(map(str, [op for op in operators.tree.service.filters if type(op) != Bind]))
        # print("making instantiation join values", filter_bag)
        if len(self.vars) >= 1:
            values_str = ' . VALUES (__vars__) { __expr__ }'
            values_str = values_str.replace('__vars__', ' '.join(['?' + v for v in self.vars]))
            combinations = []
            for tuple in filter_bag:
                combination = []
                for var in self.vars:
                    record = tuple[var]
                    if record['type'] == 'uri':
                        combination.append('<' + record['value'] + '>')
                    elif record['type'] == 'typed-literal':
                        combination.append(record['value'] + '^^<' + record['datatype'] + '>')
                    else:
                        combination.append(record['value'])
                combinations.append('(' + ' '.join(combination) + ')')
            filter_str += values_str.replace('__expr__', ' '.join(combinations))
        new_operator = operators.instantiateFilter(set(new_vars), filter_str)
        # print("type(new_operator)", type(new_operator))

        return new_operator

    def probeAndInsert1(self, tuple, table1, table2, time):
        # print("in probeAndInsert1", tuple)
        record = Record(tuple, time, 0)
        r = self.getResource(tuple)
        # print("resource", r, tuple)
        if r in table1:
            records =  table1[r]
            for t in records:
                if t.ats > record.ats:
                    continue
                x = t.tuple.copy()
                x.update(tuple)
                self.qresults.put(x)
        p = table2.get(r, [])
        i = (p == [])
        p.append(record)
        table2[r] = p
        return i

    def probeAndInsert2(self, resource, tuple, table1, table2, time):
        # print("probeAndInsert2", resource, tuple)
        record = Record(tuple, time, 0)
        if resource in table1:
            records =  table1[resource]
            for t in records:
                if t.ats > record.ats:
                    continue
                x = t.tuple.copy()
                x.update(tuple)
                self.qresults.put(x)
        p = table2.get(resource, [])
        p.append(record)
        table2[resource] = p