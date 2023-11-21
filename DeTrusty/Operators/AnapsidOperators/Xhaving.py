"""
Created on 10/12/2021.

Implements the Xhaving operator.
The intermediate results are represented in a queue.

@author: Avellino
"""

from multiprocessing import Queue
from .Xexpression import simplifyExp

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
            valid = simplifyExp(self.having, tuple)
            if valid[0] == True:
                self.qresults.put(tuple)
            tuple = self.left.get(True)
        self.qresults.put("EOF")
        return
