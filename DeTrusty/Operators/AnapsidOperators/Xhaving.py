"""
Created on 10/12/2021.

Implements the Xhaving operator.
The intermediate results are represented in a queue.

@author: Avellino
"""

from multiprocessing import Queue
from DeTrusty.Sparql.Parser.services import HavingHelper

class Xhaving(object):

    name = "HAVING"

    def __init__(self, having):
        self.qresults = Queue()                                         # end res.
        self.having = having                                            # HAVING vars
    
    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)

        while tuple != "EOF":
            valid = execute_logic(tuple, self.having)
            if valid:
                self.qresults.put(tuple)
            tuple = self.left.get(True)
        self.qresults.put("EOF")
        return

def execute_logic(tup, constrain):
    bool_ls = list()

    for arg in constrain.args:
        if type(arg) is HavingHelper:
            bool_ls.append(execute_single(tup, arg))
        else:
            bool_ls.append(execute_logic(tup, arg))

    if constrain.log_op == 'AND':
        for el in bool_ls:
            if el is False:
                return False
        return True
    else:
        for el in bool_ls:
            if el is True:
                return True
        return False

def execute_single(tup, constrain):

            if constrain.op == 'EQUALS':
                if float(tup[constrain.agg.getName()]) == float(constrain.num):
                    return True
                return False 
                    
            elif constrain.op == 'NEQUALS':
                if float(tup[constrain.agg.getName()]) != float(constrain.num):
                    return True
                return False 

            elif constrain.op == 'GREATER':
                if float(tup[constrain.agg.getName()]) > float(constrain.num):
                    return True
                return False
            
            elif constrain.op == 'GREATEREQ':
                if float(tup[constrain.agg.getName()]) >= float(constrain.num):
                    return True
                return False

            elif constrain.op == 'LESS':
                if float(tup[constrain.agg.getName()]) < float(constrain.num):
                    return True
                return False

            elif constrain.op == 'LESSEQ':
                if float(tup[constrain.agg.getName()]) <= float(constrain.num):
                    return True
                return False
