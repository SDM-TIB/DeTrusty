import datetime
from multiprocessing import Queue

from DeTrusty.Sparql.Parser.services import Argument

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

UNDEF = Argument('UNDEF')


class Xvalues(object):

    name = "VALUES"

    def __init__(self, values): 
        self.input = Queue()
        self.qresults = Queue()
        self.values = values
        self.left = None

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        tuple_ = self.left.get(True)

        while tuple_ != "EOF":
            should_include = self.filterByValues(tuple_)
            if should_include:
                self.qresults.put(tuple_)

            tuple_ = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def filterByValues(self, tuple_):
        for row in self.values.data_block_val:
            is_valid = True
            for idx, variable in enumerate(self.values.var): 
                value = tuple_[variable.name[1:]]['value']
                row_arg = row[idx]
                if row_arg == UNDEF:
                    continue 
                extracted_row_value = self.extractValue(row_arg.name)
                row_value = extracted_row_value[1:-1]
                
                if value != row_value:
                    is_valid = False
                    break
            if is_valid:
                return True
        return False 

    def extractValue(self, val):
        pos = val.find("^^")
        # Handles when the literal is typed.
        if pos > -1:
            for t in data_types.keys():
                if t in val[pos:]:
                    (python_type, general_type) = data_types[t]
                    if general_type == bool:
                        return val[:pos]
                    else:
                        return python_type(val[:pos])
        else:
            return str(val)
