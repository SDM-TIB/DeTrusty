"""
Created on Mar 03, 2014

Implements the Xorderby operator.
The intermediate results are represented in a queue.

@author: Maribel Acosta Deibe
"""

from multiprocessing import Queue
import datetime

data_types = {
    'integer': (int, 'numerical'),
    'decimal': (float, 'numerical'),
    'float': (float, 'numerical'),
    'double': (float, 'numerical'),
    'string': (str, str),
    'boolean': (bool, bool),
    'dateTime': (datetime, datetime),
    'nonPositiveInteger': (int, 'numerical'),
    'negativeInteger': (int, 'numerical'),
    'long': (int, 'numerical'),
    'int': (int, 'numerical'),
    'short': (int, 'numerical'),
    'byte': (bytes, bytes),
    'nonNegativeInteger': (int, 'numerical'),
    'unsignedLong': (int, 'numerical'),
    'unsignedInt': (int, 'numerical'),
    'unsignedShort': (int, 'numerical'),
    'unsignedByte': (bytes, bytes),  # TODO: this is not correct
    'positiveInteger': (int, 'numerical')
}


class Xorderby(object):

    name = "ORDER BY"

    def __init__(self, args):
        self.input = Queue()
        self.qresults = Queue()
        self.args = args  # List of type Argument.
        # print "self.args", self.args

    def execute(self, left, dummy, out, processqueue=Queue()):
        # Executes the Xorderby.
        self.left = left
        self.qresults = out
        results = []
        results_copy = []

        # Read all the results.
        tuple_ = self.left.get(True)
        # print "tuple", tuple_
        tuple_id = 0
        while tuple_ != "EOF":
            results_copy.append(tuple_)
            res = {}
            res.update(tuple_)
            # print "tuple", tuple_
            for arg in self.args:
                res.update({arg.name[1:]: self.extractValue(tuple_[arg.name[1:]])})
            res.update({'__id__': tuple_id})
            results.append(res)
            tuple_id = tuple_id + 1
            tuple_ = self.left.get(True)

        # Sorting.
        self.args.reverse()
        # print "en order by ",self.args
        for arg in self.args:
            order_by = "lambda d: (d['" + arg.name[1:] + "'])"
            results = sorted(results, key=eval(order_by), reverse=arg.desc)

        # Add results to output queue.
        for tuple_ in results:
            self.qresults.put(results_copy[tuple_['__id__']])

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
        return

    def extractValue(self, val):
        if val['type'] == 'literal' or val['type'] == 'uri':
            return val['value']
        elif val['type'] == 'typed-literal':
            datatype = val['datatype'].lstrip('http://www.w3.org/2001/XMLSchema#')
            python_type, general_type = data_types[datatype]
            if general_type == bool:
                return val['value']
            else:
                return python_type(val['value'])
        else:
            raise Exception("Unknown value type '%s'" % (val['type'], ))
