"""
Created on 10/12/2021.

Implements the Xaggregate operator.
The intermediate results are represented in a queue.

@author: Avellino
"""

from DeTrusty.Sparql.Parser.services import getPrefs, Expression
from multiprocessing import Queue
import operator
import datetime

unary_operators = {
    '!': operator.not_,
    '+': '',
    '-': operator.neg
}

logical_connectives = {
    '||': operator.or_,
    '&&': operator.and_
}

arithmetic_operators = {
    '*': operator.mul,
    '/': operator.truediv,
    '+': operator.add,
    '-': operator.sub
}

test_operators = {
    '=': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '>': operator.gt,
    '<=': operator.le,
    '>=': operator.ge
}

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
    'unsignedByte': (bytes, bytes)  # TODO: this is not correct
}

numerical = (int, float)

class Xaggregate(object):

    def __init__(self, args, over_all_triples, group_args, prefs):
        self.qresults = Queue()
        self.ban_list = list()
        self.one_res = dict()
        self.args = args
        self.prefsDict = getPrefs(prefs)
        
        for arg in args:
            self.ban_list.append(arg.getName())
            if over_all_triples:
                self.one_res.update({arg.getName(): arg.getDefVal()})

        for arg in group_args: # TODO: adjust after GROUP BY parser accepts Expression
            if arg.alias:
                self.ban_list.append(arg.alias[1:])
            else:
                self.ban_list.append(arg.name[1:])

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left
        self.qresults = out
        tuple = self.left.get(True)
        
        while tuple != "EOF":
            for arg in self.args:
                if type(arg.exp) is Expression:
                    self.exec_simplifyExp(arg.exp, tuple) # TODO: update tuple with return value
                else:
                    self.exec_simplifiedExp(arg.exp, arg.distinct, arg.op, arg.getName(), arg.sep, tuple)
            if not self.one_res: 
                self.qresults.put(tuple)
            tuple = self.left.get(True)

        if self.one_res:
            for arg in self.args:

                if arg.op.upper() == 'COUNT':
                    self.one_res.update({arg.getName(): str(len(self.one_res[arg.getName()]))})

                elif arg.op.upper() == 'GROUP_CONCAT':
                    if self.one_res[arg.getName()]:
                        tmp = str(self.one_res[arg.getName()])
                        if arg.sep:
                            tmp1 = tmp.replace("'", "")
                            ret = tmp1.replace(", ", arg.sep[1:len(arg.sep)-1])
                        else:
                            ret = tmp.replace("'", "")
                        self.one_res.update({arg.getName(): ret[1:len(ret)-1]})
                    else:
                        self.one_res.update({arg.getName(): ''})

                elif arg.op.upper() == 'SAMPLE':
                    if self.one_res[arg.getName()]:
                        self.one_res.update({arg.getName(): str(self.one_res[arg.getName()])})
                    else:
                        self.one_res.update({arg.getName(): ''})

                elif arg.op.upper() == 'SUM':
                    if self.one_res[arg.getName()]:
                        ret = 0
                        str_in_ls = False
                        for val in self.one_res[arg.getName()]:
                            if val.isdigit():
                                ret += int(val)
                            elif val.replace('.','', 1).isdigit():
                                ret += float(val)
                            else:
                                str_in_ls = True
                        if str_in_ls:
                            self.one_res.update({arg.getName(): ''})
                        else:
                            self.one_res.update({arg.getName(): str(ret)})
                    else:
                        self.one_res.update({arg.getName(): ''})

                elif arg.op.upper() == 'MIN':
                    if self.one_res[arg.getName()]:
                        self.one_res[arg.getName()].sort()
                        self.one_res.update({arg.getName(): str(self.one_res[arg.getName()][0])})
                    else:
                        self.one_res.update({arg.getName(): ''})

                elif arg.op.upper() == 'MAX':
                    if self.one_res[arg.getName()]:
                        self.one_res[arg.getName()].sort(reverse=True)
                        self.one_res.update({arg.getName(): str(self.one_res[arg.getName()][0])})
                    else:
                        self.one_res.update({arg.getName(): ''})

                elif arg.op.upper() == 'AVG':
                    if self.one_res[arg.getName()]:
                        ret = 0
                        str_in_ls = False
                        for val in self.one_res[arg.getName()]:
                            if val.isdigit():
                                ret += int(val)
                            elif val.replace('.', '', 1).isdigit():
                                ret += float(val)
                            else:
                                str_in_ls = True
                        if str_in_ls:
                            self.one_res.update({arg.getName(): ''})
                        else:
                            self.one_res.update({arg.getName(): str(ret/len(self.one_res[arg.getName()]))})
                    else:
                        self.one_res.update({arg.getName(): ''})

            self.qresults.put(self.one_res)
        self.qresults.put("EOF")
        return

    def exec_simplifyExp(self, arg, tup):
        if type(arg) is Expression:
            if arg.op in arithmetic_operators:
                return self.evaluateAritmethic(arg, tup)
            elif arg.op in unary_operators:
                return self.evaluateUnaryOperator(arg, tup)
            elif arg.op in test_operators:
                return self.evaluateTest(arg, tup)
            elif arg.op in logical_connectives:
                return self.evaluateLogicalConnective(arg)
        else:
            if arg.constant:
                if (arg.name[0] == '<' and arg.name[len(arg.name)-1] == '>') or ((arg.name[0] == "'" and arg.name[len(arg.name)-1] == "'") or (arg.name[0] == '"' and arg.name[len(arg.name)-1] == '"')):
                    return arg.name[1:len(arg.name)-1]
                elif ":" in arg.name:
                    pos = arg.name.find(":")
                    c = arg.name[0:pos].strip()
                    v = arg.name[(pos+1):len(arg.name)].strip()
                    if c in self.prefsDict:
                        return self.prefsDict[c][1:len(self.prefsDict[c])-1] + v
                    else: # TODO: throw exception
                        pass
                else:
                    return arg.name
            else:
                return tup[arg.name[1:]]

    def evaluateAritmethic(self, arg, tup):
        term_left = str(self.exec_simplifyExp(arg.left, tup))
        term_right = str(self.exec_simplifyExp(arg.right, tup))
        if term_left.isdigit() and term_right.isdigit():
            term_left = int(term_left)
            term_right = int(term_right)
            return (arithmetic_operators[operator](term_left, term_right))
        elif term_right.replace('.','',1).isdigit() and term_left.isdigit():
            term_right = float(term_right)
            term_left = int(term_left)
            return (arithmetic_operators[operator](term_left, term_right))
        elif term_left.replace('.','',1).isdigit() and term_right.isdigit():
            term_left = float(term_left)
            term_right = int(term_right)
            return (arithmetic_operators[operator](term_left, term_right))
        elif term_left.replace('.','',1).isdigit() and term_right.replace('.','',1).isdigit():
            term_left = float(term_left)
            term_right = float(term_right)
            return (arithmetic_operators[operator](term_left, term_right))
        else:
            raise SPARQLTypeError

    def evaluateUnaryOperator(self, arg, tup):
        term_left = exec_simplifyExp(arg.left, tup)
        return unary_operators[arg.op](term_left)

    def evaluateTest(self, arg, tup):
        left = exec_simplifyExp(arg.left)
        right = exec_simplifyExp(arg.right)
        (term_left, type_left) = left, type(left)
        (term_right, type_right) = right, type(right)
        term_left = str(term_left)
        term_right = str(term_right)
        if term_left.isnumeric() and term_right.isnumeric():
            term_left = int(term_left)
            term_right = int(term_right)
            return (test_operators[operator](term_left, term_right), bool)
        elif term_left.replace('.','',1).isdigit() and term_right.isnumeric():
            term_left = float(term_left)
            term_right = int(term_right)
            return (test_operators[operator](term_left, term_right), bool)
        elif term_left.isnumeric() and term_right.replace('.','',1).isdigit():
            term_left = int(term_left)
            term_right = float(term_right)
            return (test_operators[operator](term_left, term_right), bool)
        elif term_left.replace('.','',1).isdigit() and term_right.replace('.','',1).isdigit():
            term_left = float(term_left)
            term_right = float(term_right)
            return (test_operators[operator](term_left, term_right), bool)
        else:
            print("SPARQLTypeError - in Xbind")
            raise SPARQLTypeError

    def exec_simplifiedExp(self, arg, dist, op, name, sep, tup):
        if arg.constant:
            if (arg.name[0] == '<' and arg.name[len(arg.name)-1] == '>') or ((arg.name[0] == "'" and arg.name[len(arg.name)-1] == "'") or (arg.name[0] == '"' and arg.name[len(arg.name)-1] == '"')):
                tup.update({name : arg.name[1:len(arg.name)-1]})
                if self.one_res:
                    if op.upper() == 'SAMPLE':
                        self.one_res[name] = arg.name[1:len(arg.name)-1]
                    elif dist:
                        if arg.name[1:len(arg.name)-1] not in self.one_res[name]:
                            self.one_res[name].append(arg.name[1:len(arg.name)-1])
                    else:
                        self.one_res[name].append(arg.name[1:len(arg.name)-1])
            elif ":" in arg.name:
                pos = arg.name.find(":")
                c = arg.name[0:pos].strip()
                v = arg.name[(pos+1):len(arg.name)].strip()
                if c in self.prefsDict:
                    tup.update({name : self.prefsDict[c][1:len(self.prefsDict[c])-1] + v})
                    if self.one_res:
                        if op.upper() == 'SAMPLE':
                            self.one_res[name] = self.prefsDict[c][1:len(self.prefsDict[c])-1] + v                        
                        elif dist:
                            if (self.prefsDict[c][1:len(self.prefsDict[c])-1] + v) not in self.one_res[name]:
                                self.one_res[name].append(self.prefsDict[c][1:len(self.prefsDict[c])-1] + v)
                        else:
                            self.one_res[name].append(self.prefsDict[c][1:len(self.prefsDict[c])-1] + v)
                else: # TODO: throw exception
                    pass
            else:
                tup.update({name : arg.name})
                if self.one_res:
                    if op.upper() == 'SAMPLE':
                        self.one_res[name] = arg.name
                    elif dist:
                        if arg.name not in self.one_res[name]:
                            self.one_res[name].append(arg.name)
                    else:
                        self.one_res[name].append(arg.name)
        else:
            if self.one_res:
                if arg.name == '?ALL':
                    if dist:
                        if tup not in self.one_res[name]:
                            self.one_res[name].append(tup)
                    else:
                        self.one_res[name].append(tup)
                elif tup[arg.name[1:]] != '':
                    if op.upper() == 'SAMPLE':
                        if not self.one_res[name]:
                            self.one_res[name] = tup[arg.name[1:]]
                    else:
                        if dist:
                            if tup[arg.name[1:]] not in self.one_res[name]:
                                self.one_res[name].append(tup[arg.name[1:]])
                        else:
                            self.one_res[name].append(tup[arg.name[1:]])
            else:
                if op.upper() == 'COUNT':
                    if arg.name == '?ALL': # TODO: how to handle distinct?
                        for arg in tup:
                            if arg not in self.ban_list:
                                if type(tup[arg]) == list:
                                    tup.update({name: str(len(tup[arg]))})
                                    break
                                else:
                                    tup.update({name: '1'})
                                    break

                    else:
                        if dist:
                            if type(tup[arg.name[1:]]) is list:
                                rec = list()
                                count = 0
                                for val in tup[arg.name[1:]]:
                                    if val not in rec and val != '':
                                        rec.append(val)
                                        count += 1
                                tup.update({name: str(count)})
                            else:
                                if tup[arg.name[1:]] == '':
                                    tup.update({name: '0'})
                                else:
                                    tup.update({name: '1'})
                                    
                        else:
                            if type(tup[arg.name[1:]]) is list:
                                count = 0
                                for val in tup[arg.name[1:]]:
                                    if val != '':
                                        count += 1
                                tup.update({name: str(count)})
                            else:
                                if tup[arg.name[1:]] == '':
                                    tup.update({name: '0'})
                                else:
                                    tup.update({name: '1'})

                elif op.upper() == 'GROUP_CONCAT':
                    if dist:
                        if type(tup[arg.name[1:]]) is list:
                            tmp = set(tup[arg.name[1:]])
                            if '' in tmp:
                                tmp.remove('')
                            if len(tmp) > 0:
                                tmp1 = str(tmp)
                                if sep:
                                    tmp2 = tmp1.replace("'", "")
                                    ret = tmp2.replace(", ", sep[1:len(sep)-1])
                                else:
                                    ret = tmp1.replace("'", "")
                                tup.update({name: ret[1:len(ret)-1]})
                            else:
                                tup.update({name: ''})
                        else:
                            tup.update({name: tup[arg.name[1:]]})
                    else:
                        if type(tup[arg.name[1:]]) is list:
                            tmp = tup[arg.name[1:]].copy()
                            while '' in tmp:
                                tmp.remove('')
                            if len(tmp) > 0:
                                tmp1 = str(tmp)
                                if sep:
                                    tmp2 = tmp1.replace("'", "")
                                    ret = tmp2.replace(", ", sep[1:len(sep)-1])
                                else:
                                    ret = tmp1.replace("'", "")
                                tup.update({name: ret[1:len(ret)-1]})
                            else:
                                tup.update({name: ''})
                        else:
                            tup.update({name: tup[arg.name[1:]]})

                elif op.upper() == 'SAMPLE':
                    if type(tup[arg.name[1:]]) is list:
                        tmp_ls = tup[arg.name[1:]]
                        found_non_empty = False
                        for val in tmp_ls:
                            if val != '':
                                tup.update({name: val})
                                found_non_empty = True
                                break
                        if not found_non_empty:
                            tup.update({name: ''})
                    else:
                        tup.update({name: tup[arg.name[1:]]})

                elif op.upper() == 'SUM':
                    if type(tup[arg.name[1:]]) is list:
                        str_in_ls = False
                        ret = 0
                        if dist:
                            tmp = list()
                            for val in tup[arg.name[1:]]:
                                if val != '' and val not in tmp:
                                    tmp.append(val)
                                    if val.isdigit():
                                        ret += int(val)
                                    elif val.replace('.','', 1).isdigit():
                                        ret += float(val)
                                    else:
                                        str_in_ls = True
                        else:
                            for val in tup[arg.name[1:]]:
                                if val != '':
                                    if val.isdigit():
                                        ret += int(val)
                                    elif val.replace('.','', 1).isdigit():
                                        ret += float(val)
                                    else:
                                        str_in_ls = True
                        if str_in_ls:
                            tup.update({name: ''})
                        else:
                            tup.update({name: str(ret)})
                    else:
                        is_num = True
                        if not tup[arg.name[1:]].replace('.', '', 1).isdigit():
                            is_num = False
                        if is_num:
                            tup.update({name: tup[arg.name[1:]]})
                        else:
                            tup.update({name: ''})
                                
                elif op.upper() == 'MIN':
                    if type(tup[arg.name[1:]]) is list:
                        tmp = None
                        if dist:
                            tmp = set(tup[arg.name[1:]])
                            if '' in tmp:
                                tmp.remove('')
                        else:
                            tmp = tup[arg.name[1:]].copy()
                            while '' in tmp:
                                tmp.remove('')
                        tmp.sort()
                        if tmp:
                            tup.update({name: str(tmp[0])})
                        else:
                            tup.update({name: ''})
                    else:
                        tup.update({name: tup[arg.name[1:]]})

                elif op.upper() == 'MAX':
                    if type(tup[arg.name[1:]]) is list:
                        tmp = None
                        if dist:
                            tmp = set(tup[arg.name[1:]])
                            if '' in tmp:
                                tmp.remove('')
                        else:
                            tmp = tup[arg.name[1:]].copy()
                            while '' in tmp:
                                tmp.remove('')
                        tmp.sort(reverse=True)
                        if tmp:
                            tup.update({name: str(tmp[0])})
                        else:
                            tup.update({name: ''})
                    else:
                        tup.update({name: tup[arg.name[1:]]})

                elif op.upper() == 'AVG':
                    if type(tup[arg.name[1:]]) is list:
                        str_in_ls = False
                        ret = 0
                        val_count = 0
                        if dist:
                            for val in tup[arg.name[1:]]:
                                if val != '' and val not in tmp:
                                    tmp.append(val)
                                    if val.isdigit():
                                        ret += int(val)
                                    elif val.replace('.','', 1).isdigit():
                                        ret += float(val)
                                    else:
                                        str_in_ls = True
                                    val_count += 1
                        else:
                            for val in tup[arg.name[1:]]:
                                if val != '':
                                    if val.isdigit():
                                        ret += int(val)
                                    elif val.replace('.','', 1).isdigit():
                                        ret += float(val)
                                    else:
                                        str_in_ls = True
                                    val_count += 1
                        if str_in_ls:
                            tup.update({name: ''})
                        else:
                            ret = ret / val_count
                            tup.update({name: str(ret)})
                    else:
                        is_num = True
                        if not tup[arg.name[1:]].replace('.', '', 1).isdigit():
                            is_num = False
                        if is_num:
                            tup.update({name: tup[arg.name[1:]]})
                        else:
                            tup.update({name: ''})
