"""
Created on 23/10/2022.

Implements the temporary handling of Expression. 
Note that this handle only Arithmetic expression for now.

@author: Avellino
"""

from DeTrusty.Sparql.Parser.services import Argument, Aggregate, Expression
import operator

arithmetic_operators = {
    '*': operator.mul,
    '/': operator.truediv,
    '+': operator.add,
    '-': operator.sub
}

def simplifyExp(exp, tuple):
    if type(exp) is Argument:
        if exp.constant: 
            if exp.name == '*':
                for el in tuple:
                    if type(el) is list:
                        return el
            return exp.name
        else:
            return tuple[exp.name[1:]]
    else:
        return evaluateOperator(exp, tuple)

def evaluateOperator(exp, tuple):

    if type(exp) is Aggregate:
        if type(exp.exp) is Expression or type(exp.exp) is Argument:
            ls = simplifyExp(exp.exp, tuple)
        return evaluateAggregate(exp.op, exp.distinct, exp.sep, ls)

    if type(exp.left) is Expression or type(exp.left) is Argument or type(exp.left) is Aggregate:
        simp_left = simplifyExp(exp.left, tuple)

    if type(exp.right) is Expression or type(exp.right) is Argument or type(exp.right) is Aggregate: 
        simp_right = simplifyExp(exp.right, tuple)

    if exp.exp_type == 'arithmetic':
        if type(simp_left) is list and type(simp_right) is list:
            ret = list()
            for el1 in simp_left:
                for el2 in simp_right:
                    ret.append(evaluateArithmetic(el1, exp.op, el2))
            return ret
        if type(simp_left) is list:
            ret = list()
            for el in simp_left:
                ret.append(evaluateArithmetic(el, exp.op, simp_right))
            return ret
        if type(simp_right) is list:
            ret = list()
            for el in simp_right:
                ret.append(evaluateArithmetic(simp_left, exp.op, el))
            return ret
        return evaluateArithmetic(simp_left, exp.op, simp_right)

def evaluateArithmetic(left, op, right):
    try:
        return arithmetic_operators[op](float(left), float(right))
    except:
        return ''

# distinction of RDF literal: https://www.w3.org/TR/rdf-concepts/#section-Literal-Equality
def evaluateAggregate(op, dist, sep, ls):

    if op.upper() == 'COUNT':
        if dist:
            rec = list()
            count = 0
            for val in ls:
                if val not in rec and val != '': 
                    rec.append(val)
                    count += 1
            return count

        else:
            count = 0
            for val in ls:
                if val != '':
                    count += 1
            return count

    if op.upper() == 'GROUP_CONCAT':
        if dist:
            tmp = set(ls)
            if '' in tmp:
                tmp.remove('')
            if len(tmp) > 0:
                tmp1 = str(tmp)
                if sep:
                    tmp2 = tmp1.replace("'", "")
                    ret = tmp2.replace(", ", sep[1:len(sep)-1])
                else:
                    ret = tmp1.replace("'", "")
                return ret[1:len(ret)-1]
            else:
                return ''
        else:
            tmp = ls.copy()
            while '' in tmp:
                tmp.remove('')
            if len(tmp) > 0:
                tmp1 = str(tmp)
                if sep:
                    tmp2 = tmp1.replace("'", "")
                    ret = tmp2.replace(", ", sep[1:len(sep)-1])
                else:
                    ret = tmp1.replace("'", "")
                return ret[1:len(ret)-1]
            else:
                return ''

    if op.upper() == 'SAMPLE':
        for val in ls:
            if val != '':
                return val
        return ''

    if op.upper() == 'MIN':
        tmp = None
        if dist:
            tmp = set(ls)
            if '' in tmp:
                tmp.remove('')
            tmp = list(tmp)
        else:
            tmp = ls.copy()
            while '' in tmp:
                tmp.remove('')
        tmp.sort()
        if tmp:
            return tmp[0]
        else:
            return ''

    if op.upper() == 'MAX':
        tmp = None
        if dist:
            tmp = set(ls)
            if '' in tmp:
                tmp.remove('')
            tmp = list(tmp)
        else:
            tmp = ls.copy()
            while '' in tmp:
                tmp.remove('')
        tmp.sort(reverse=True)
        if tmp:
            return tmp[0]
        else:
            return ''

    if op.upper() == 'SUM':
        ret = 0
        if dist:
            tmp = list()
            for val in ls:
                if val != '' and val not in tmp:
                    tmp.append(val)
                    try:
                        ret += float(val)
                    except:
                        return ''
        else:
            for val in ls:
                if val != '':
                    try:
                        ret += float(val)
                    except:
                        return ''
        return ret

    if op.upper() == 'AVG':
        ret = 0
        val_count = 0
        if dist:
            tmp = list()
            for val in ls:
                if val != '' and val not in tmp:
                    tmp.append(val)
                    try:
                        ret += float(val)
                    except:
                        return ''
                    val_count += 1
        else:
            for val in ls:
                if val != '':
                    try:
                        ret += float(val)
                    except:
                        return ''
                    val_count += 1
        if val_count != 0:
            ret = ret / val_count
        return ret
