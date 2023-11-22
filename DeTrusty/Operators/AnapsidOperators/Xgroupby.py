"""
Created on 30/08/2021.

Implements the Xgroupby operator.
The intermediate results are represented in a queue.

@author: Avellino
"""

from multiprocessing import Queue


class Xgroupby(object):

    name = 'GROUP BY'

    def __init__(self, args, over_all_triple):
        self.qresults = Queue()                                            # end res.
        self.args = args                                                   # GROUP BY vars
        self.overall = over_all_triple

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        arg_list = list()
        tmp = list()                                                       # [tup1,tup2,...]

        if self.overall:
            tuple_ = self.left.get(True)
            ret = dict()
            for var in tuple_:
                ret.update({var: [tuple_[var]]})
            tuple_ = self.left.get(True)
            while tuple_ != 'EOF':
                for var in tuple_.keys():
                    ret[var].append(tuple_[var])
                tuple_ = self.left.get(True)
            self.qresults.put(ret)
            self.qresults.put('EOF')
            return

        for arg in self.args:
            arg_list.append(arg.name[1:])
            if arg.alias:
                arg_list.append(arg.alias[1:])

        tuple_ = self.left.get(True)

        while tuple_ != 'EOF':
            match = [0] * len(tmp)
            append = True

            for i in range(len(tmp)):
                tmp_dict = tmp[i]
                for arg in self.args:                                       # type(arg) always Argument
                    if arg.alias is not None:
                        if tuple_[arg.name[1:]] == tmp_dict[arg.alias[1:]]:
                            match[i] += 1                                   # record matches based on tmp index
                    else:
                        if tuple_[arg.name[1:]] == tmp_dict[arg.name[1:]]:
                            match[i] += 1

            for j in range(len(match)):
                if match[j] == len(self.args): 
                    append = False
                    for var in tuple_:
                        if var not in arg_list:
                            tmp_dict = tmp[j]
                            if var not in tmp_dict.keys():
                                tmp_dict[var] = []
                            tmp_dict[var].append(tuple_[var])

            if append:
                for arg in self.args:
                    if arg.alias is not None:
                        tuple_.update({arg.alias[1:]: tuple_[arg.name[1:]]})
                for key in tuple_:
                    if key not in arg_list:
                        tuple_.update({key: [tuple_[key]]})
                tmp.append(tuple_)

            tuple_ = self.left.get(True)

        tmp.reverse()
        while tmp:
            self.qresults.put(tmp.pop())
        self.qresults.put('EOF')
        return
