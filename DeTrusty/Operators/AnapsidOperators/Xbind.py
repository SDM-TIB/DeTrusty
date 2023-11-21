from multiprocessing import Queue
from .Xexpression import simplifyExp, translateToDict

class Xbind(object):

    name = "BIND"

    def __init__(self, bind):
        self.input = Queue()
        self.qresults = Queue()
        self.bind = bind

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left 
        self.qresults = out
        b_value = self.bind.expr
        b_var = self.bind.alias[1:]
        tuple = self.left.get(True)
        while (tuple != "EOF"):
            tuple.update({b_var: translateToDict(simplifyExp(b_value, tuple))})
            tuple = self.left.get(True)
            self.qresults.put(tuple)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")
