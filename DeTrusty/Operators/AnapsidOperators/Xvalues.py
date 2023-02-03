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


class Xvalues(object):

    name = "VALUES"

    def __init__(self, values): 
        self.input = Queue()
        self.qresults = Queue()
        self.values = values  

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)

        while (tuple != "EOF"):
            shouldInclude = self.filterByValues(tuple)
            if shouldInclude:
                self.qresults.put(tuple)

            tuple = self.left.get(True)           

        # Put EOF in queue and exit.
        self.qresults.put("EOF")

    def filterByValues(self, tuple):        
        for row in self.values.data_block_val:
            isValid = True
            for idx, variable in enumerate(self.values.var): 
                value = tuple[variable.name[1:]]
                rowArg = row[idx]
                if rowArg is None:
                    continue 
                extractedRowValue = self.extractValue(rowArg.name)
                rowValue = extractedRowValue[1:-1]
                
                if value != rowValue:
                    isValid = False
                    break
            if isValid:
                return True
        return False 

    def extractValue(self, val):
        pos = val.find("^^")
        # Handles when the literal is typed.
        if (pos > -1):
            for t in data_types.keys():
                if (t in val[pos:]):
                    (python_type, general_type) = data_types[t]
                    if (general_type == bool):
                        return val[:pos]
                    else:
                        return python_type(val[:pos])
        else:
            return str(val)
