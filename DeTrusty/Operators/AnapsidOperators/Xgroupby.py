"""
Created on 30/08/2021.

Implements the Xgroupby operator.
The intermediate results are represented in a queue.

@author: Avellino
"""

# TODO: the grouping is quite wrong in case of implicit grouping, reference: 18.2.4.1 in spec.
from multiprocessing import Queue

class Xgroupby(object):                                                    # ensure backward comp.

    name = "GROUP BY"

    def __init__(self, args):
        self.qresults = Queue()                                            # end res.
        self.args = args                                                   # GROUP BY vars

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        arg_list = list()
        tmp = list()                                                       # [tup1,tup2,...]

        for arg in self.args:
            arg_list.append(arg.name[1:])

        tuple = self.left.get(True)

        while (tuple != "EOF"):
            match = [0] * len(tmp)
            append = True

            for i in range(len(tmp)):
                tmp_dict = tmp[i]
                for arg in self.args:                                       # type(arg) always Argument
                    if arg.alias is not None:
                        if tuple[arg.name[1:]] == tmp_dict[arg.alias[1:]]:
                            match[i] += 1                                   # record matches based on tmp index
                    else:
                        if tuple[arg.name[1:]] == tmp_dict[arg.name[1:]]:
                            match[i] += 1

            for j in range(len(match)):
                if match[j] == len(self.args): 
                    append = False
                    for var in tuple:
                        if var not in arg_list:
                            tmp_dict = tmp[j]
                            tmp_dict[var].append(tuple[var])

            if append:
                for arg in self.args:
                    if arg.alias is not None:
                        tuple.update({arg.alias[1:]: tuple[arg.name[1:]]})
                for key in tuple:
                    if key not in arg_list:
                        tuple.update({key: [tuple[key]]})
                tmp.append(tuple)

            tuple = self.left.get(True)

        ###DEBUG###
        # print("GROUP BY vars:", arg_list)
        # for i in range(len(tmp)):
            # tmp_dict = tmp[i]
            # for attr in tmp_dict:
                # string = attr + ": " 
                # if type(tmp_dict[attr]) == list:
                    # string = string + str(len(tmp_dict[attr]))
                # else:
                    # string = string + tmp_dict[attr]
                # print(string)

        tmp.reverse()
        while tmp:
            self.qresults.put(tmp.pop())
        self.qresults.put("EOF")
        return
