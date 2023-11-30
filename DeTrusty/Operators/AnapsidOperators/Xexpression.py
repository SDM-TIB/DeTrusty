"""
Created on 26/09/2022.

Implements the Xexpression module.
The result is triple consisting of value, type, datatype.

@author: Avellino
"""

from DeTrusty.Sparql.Parser.services import Argument, Aggregate
from dateutil.parser import * 
import operator

arithmetic_operators = {
    '*': operator.mul,
    '/': operator.truediv,
    '+': operator.add,
    '-': operator.sub
}

logical_connectives = {
    '||': operator.or_,
    '&&': operator.and_
}

test_operators = {
    '=': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '>': operator.gt,
    '<=': operator.le,
    '>=': operator.ge,
}

xsd = "http://www.w3.org/2001/XMLSchema#"

# TODO: handle other derived types?
data_types = {
    xsd + 'integer': int,
    xsd + 'decimal': float,
    xsd + 'float': float,
    xsd + 'double': float,
    xsd + 'string': str,
    xsd + 'boolean': bool,
    xsd + 'dateTime': parse,
    # from numeric derived types
    xsd + 'nonPositiveInteger': int,
    xsd + 'negativeInteger': int,
    xsd + 'long': int,
    xsd + 'int': int,
    xsd + 'short': int,
    xsd + 'byte': int,
    xsd + 'nonNegativeInteger': int,
    xsd + 'unsignedLong': int,
    xsd + 'unsignedInt': int,
    xsd + 'unsignedShort': int,
    xsd + 'unsignedByte': int,
    xsd + 'positiveInteger': int,
    # additional datatypes (need further testing)
    xsd + 'anyURI': str
}

def simplifyExp(exp, tuple):
    if type(exp) is Argument:
        if exp.constant: 
            try:
                return data_types.get(exp.datatype.strip('<>'))(exp.name.strip('\"').strip('\'')), exp.gen_type, exp.datatype.strip('<>') 
            except:
                if exp.gen_type == 'literal' or exp.gen_type == 'uri' or exp.name.strip("\'").strip("\"") == '':
                    return exp.name.strip('\'').strip('\"'), exp.gen_type, exp.datatype
                return None, None, None  # in case of mismatch
        else:
            if exp.name != '*':
                return extractValue(tuple[exp.name[1:]])
            else:
                for var in tuple:
                    if not isinstance(tuple[var], list):
                        continue
                    return extractValue(tuple[var])
                return None, None, None  # in case no grouped variables exist
    else:
        return evaluateOperator(exp, tuple)


# order of evaluation is important here! TODO: test and recheck
def evaluateOperator(exp, tuple_):
    if isinstance(exp, Aggregate):  # grouped aggregate only
        if not isinstance(exp.exp, tuple) and not isinstance(exp.exp, list):
            extracted = simplifyExp(exp.exp, tuple_)
        return evaluateAggregate(exp, extracted)

    #  if exp.exp_type == 'builtInNil': # add operators that requires no input here, for example RAND()
        #  return '', None, None

    if type(exp.left) is not tuple and type(exp.left) is not list:
        extracted_left = simplifyExp(exp.left, tuple_)

    if exp.exp_type == 'unary':
        if type(extracted_left) is list:
            ret = list()
            for el in extracted_left:
                ret.append(evaluateUnaryOperator(el, exp.op))
            return ret
        return evaluateUnaryOperator(extracted_left, exp.op)

    if exp.exp_type == 'builtInUnary':
        if type(extracted_left) is list:
            ret = list()
            for el in extracted_left:
                ret.append(evaluateBuiltInUnary(el, exp.op))
            return ret
        return evaluateBuiltInUnary(extracted_left, exp.op)

    if (type(exp.right) is not tuple and type(exp.right) is not list): 
        extracted_right = simplifyExp(exp.right, tuple_)

    if exp.exp_type == 'arithmetic':
        if type(extracted_left) is list and type(extracted_right) is list:
            ret = list()
            for el1 in extracted_left:
                for el2 in extracted_right:
                    ret.append(evaluateArithmetic(el1, exp.op, el2))
            return ret
        if type(extracted_left) is list:
            ret = list()
            for el in extracted_left:
                ret.append(evaluateArithmetic(el, exp.op, extracted_right))
            return ret
        if type(extracted_right) is list:
            ret = list()
            for el in extracted_right:
                ret.append(evaluateArithmetic(extracted_left, exp.op, el))
            return ret
        return evaluateArithmetic(extracted_left, exp.op, extracted_right)

    if exp.exp_type == 'relational':
        if exp.op.upper() == 'IN':
            extracted_right = list()
            for el in exp.right:
                extracted_right.append(simplifyExp(el, tuple_))
            if type(extracted_left) is list:
                ret = list()
                for el in extracted_left:
                    ret.append(evaluateTest(el, exp.op, extracted_right))
                return ret
            return evaluateTest(extracted_left, exp.op, extracted_right)
        if type(extracted_left) is list and type(extracted_right) is list:
            ret = list()
            for el1 in extracted_left:
                for el2 in extracted_right:
                    ret.append(evaluateTest(el1, exp.op, el2))
            return ret
        if type(extracted_left) is list:
            ret = list()
            for el in extracted_left:
                ret.append(evaluateTest(el, exp.op, extracted_right))
            return ret
        if type(extracted_right) is list:
            ret = list()
            for el in extracted_right:
                ret.append(evaluateTest(extracted_left, exp.op, el))
            return ret
        return evaluateTest(extracted_left, exp.op, extracted_right)

    if exp.exp_type == 'logical':
        if type(extracted_left) is list and type(extracted_right) is list:
            ret = list()
            for el1 in extracted_left:
                for el2 in extracted_right:
                    ret.append(evaluateLogicalConnective(el1, exp.op, el2))
            return ret
        if type(extracted_left) is list:
            ret = list()
            for el in extracted_left:
                ret.append(evaluateLogicalConnective(el, exp.op, extracted_right))
            return ret
        if type(extracted_right) is list:
            ret = list()
            for el in extracted_right:
                ret.append(evaluateLogicalConnective(extracted_left, exp.op, el))
            return ret
        return evaluateLogicalConnective(extracted_left, exp.op, extracted_right)

    # TODO: adding more coverages later on
    return ('', None, None)

def evaluateArithmetic(left, op, right):

    val_left, left_type, xsl_type = left
    val_right, right_type, xsr_type = right

    try:
        ret = arithmetic_operators[op](val_left, val_right)
        if type(ret) == float:
            return (ret, 'typed-literal', xsd + 'decimal')
        elif type(ret) == int :
            return (ret, 'typed-literal', xsd + 'integer')
        return ret, 'literal', None 
    except:
        return ('', None, None)

def evaluateUnaryOperator(left, op):

    val, gen_type, xsd_type = left

    if op == '!':
        if gen_type is not bool:
            return (not evaluateEBV(left)[0], 'typed-literal', xsd + 'boolean')
        else:
            return (not val, gen_type, xsd_type)

    if op == '+':
        if xsd_type == xsd + 'integer' or xsd_type == xsd + 'decimal':
            return (val, gen_type, xsd_type)
        else:
            return ('', None, None)

    if op == '-':
        if xsd_type == xsd + 'integer' or xsd_type == xsd + 'decimal':
            return (0 - val, gen_type, xsd_type)
        else:
            return ('', None, None)

def evaluateTest(left, op, right):

    if op.upper() == "IN":
        for ex in right:
            if left[0] == ex[0]: # TODO: test, whether such comparison of tuple working flawlessly or not
                return (True, 'typed-literal', xsd + 'boolean')
        return (False, 'typed-literal', xsd + 'boolean')

    val_left, left_type, xsl_type = left
    val_right, right_type, xsr_type = right

    try: 
        return (test_operators[op](val_left, val_right), 'typed-literal', xsd + 'boolean') # TODO: test, and check whether it covers the spec. completely or not
    except :
        return '', None, None

def evaluateLogicalConnective(left, op, right):

    val_left, left_type, xsl_type = left
    val_right, right_type, xsr_type = right

    try:
        return (logical_connectives[op](val_left, val_right), 'typed-literal', xsd + 'boolean')
    except:
        return '', None, None


def evaluateBuiltInUnary(left, op): 

    val, gen_type, xsd_type = left
    if op.upper() == 'YEAR':
        if xsd_type == xsd + 'dateTime':
            return (val.year, 'typed-literal', xsd + 'integer')
        else:
            return '', None, None

    if op.upper() == 'DATATYPE':
        if xsd_type is not None:
            return (xsd_type, 'uri', None)
        else:
            return '', None, None


# distinction of RDF literal: https://www.w3.org/TR/rdf-concepts/#section-Literal-Equality
def evaluateAggregate(agg, extracted): # type(extracted) always list <-> automatic grouping if necessary. This supposed to reduce time complexity, by reducing comparison

    op, dist, sep = agg.op, agg.distinct, agg.sep 

    ignored = list() # list of ignored values, not sure if this correct.
    ignored.append('') # optional, or error value
    ignored.append(None) # mismatch between provided xsd and value (cannot be casted into)

    if op.upper() == 'COUNT':
        count = 0
        if dist:
            rec = list()
            rec += ignored
            for val in extracted:
                if val[0] not in rec: # depend only on the value, not respecting the gen_type and xsd_type, correct? Yes, from prev. discussion
                    rec.append(val[0])
                    count += 1
            return (count, 'typed-literal', xsd + 'integer')

        else:
           # print('extracted:', extracted)

            for val in extracted:
                if val[0] not in ignored:
                    count += 1
            return (count, 'typed-literal', xsd + 'integer')


    elif op.upper() == 'GROUP_CONCAT':
        tmp = list()
        if dist:
            for val in extracted:
                if val[0] not in ignored:
                    tmp.append(val[0])
            tmp = str(set(tmp)).strip('{}')
            if sep:
                tmp1 = tmp.replace("'", "")
                ret = tmp1.replace(", ", sep[1:len(sep)-1])
            else:
                ret = tmp.replace("'", "")
            return ret, 'literal', None
        else:
            for val in extracted:
                if val[0] not in ignored:
                    tmp.append(val[0])
            tmp = str(tmp).strip('[]')
            if sep:
                tmp1 = tmp.replace("'", "")
                ret = tmp1.replace(", ", sep[1:len(sep)-1])
            else:
                ret = tmp.replace("'", "")
            return ret, 'literal', None


    elif op.upper() == 'MIN':
        tmp = list(val[0] for val in extracted if val[0] not in ignored) 
        try:
            ret = min(tmp)
            if type(ret) is float:
                return ret, 'typed-literal', xsd + 'decimal'
            elif type(ret) is int:
                return ret, 'typed-literal', xsd + 'integer'
            return ret, 'literal', None # this is not quite correct according spec. Supposed to check every xsd_type of val in extracted to determine output xsd_type 
        except:
            return '', None, None

    elif op.upper() == 'MAX':
        tmp = list(val[0] for val in extracted if val[0] not in ignored) 
        try:
            ret = max(tmp)
            if type(ret) is float:
                return ret, 'typed-literal', xsd + 'decimal'
            elif type(ret) is int:
                return ret, 'typed-literal', xsd + 'integer'
            return ret, 'literal', None # this is not quite correct according spec. Supposed to check every xsd_type of val in extracted to determine output xsd_type 
        except:
            return '', None, None

    elif op.upper() == 'AVG':
        tmp = list(val[0] for val in extracted if val[0] not in ignored)
        if dist:
            tmp = set(tmp)
            try:
                ret = sum(tmp)/len(tmp)
                if type(ret) is float:
                    return ret, 'typed-literal', xsd + 'decimal'
                return ret, 'typed-literal', xsd + 'integer'
            except:
                return '', None, None
        else:
            try:
                ret = sum(tmp)/len(tmp)
                if type(ret) is float:
                    return ret, 'typed-literal', xsd + 'decimal'
                return ret, 'typed-literal', xsd + 'integer'
            except:
                return '', None, None

    elif op.upper() == 'SAMPLE':
        for el in extracted: 
            if el[0] not in ignored:
                return el[0], el[1], el[2]

    elif op.upper() == 'SUM':
        tmp = list(val[0] for val in extracted if val[0] not in ignored)
        if dist:
            tmp = set(tmp)
        try:
            ret = sum(tmp)
            if type(ret) is float:
                return ret, 'typed-literal', xsd + 'decimal'
            return ret, 'typed-literal', xsd + 'integer'
        except:
            return '', None, None


'''
evaluateEBV: calculates whether an argument is an Effective Boolean Value (EBV)
             according to the definition in the SPARQL documentation 
             See: http://www.w3.org/TR/sparql11-query/#ebv and https://www.w3.org/TR/xpath-functions/#func-boolean
'''

def evaluateEBV(value):
    (val, val_type, xsd_type) = value

    # The EBV of any literal whose type is xsd:boolean or numeric is false if the lexical form is not valid for that datatype (e.g. "abc"^^xsd:integer).
    if val in ['', None]:
        return (False, 'typed-literal', xsd + 'boolean')

    # If $arg is a singleton value of type xs:boolean or a derived from xs:boolean, fn:boolean returns $arg.
    if (type(val) is bool):
        return (val, val_type, xsd_type)

    # If $arg is a singleton value of type xs:string or a type derived from xs:string, xs:anyURI or a type derived from xs:anyURI, or xs:untypedAtomic, fn:boolean returns false if the operand value has zero length; otherwise it returns true.
    # If the argument is a plain literal or a typed literal with a datatype of xsd:string, the EBV is false if the operand value has zero length; otherwise the EBV is true.
    if val_type == 'literal':
        if len(val) != 0:
            return (True, 'typed-literal', xsd + 'boolean')
        return (False, 'typed-literal', xsd + 'boolean')

    # If $arg is a singleton value of any numeric type or a type derived from a numeric type, fn:boolean returns false if the operand value is NaN or is numerically equal to zero; otherwise it returns true.
    if (val_type == 'typed-literal'):
        if val == 0 or val == 'NaN':
            return (False, 'typed-literal', xsd + 'boolean')
        return (True, 'typed-literal', xsd + 'boolean')

    # other cases
    return ('', None, None)


def extractValue(val):
    if type(val) is list:
        tmp = list()
        for el in val:
            if el.get('type') == 'literal' or el.get('type') == 'uri' or el.get('value') == '':
                tup = el.get('value'), el.get('type'), el.get('datatype')
                tmp.append(tup)
            else:
                try:
                    tup = data_types.get(el.get('datatype'))(el.get('value')), el.get('type'), el.get('datatype')
                    tmp.append(tup)
                except:
                    tup = None, None, None
                    tmp.append(tup)
        return tmp
    else:
        if val.get('type') == 'literal' or val.get('type') == 'uri' or val.get('value') == '':
            return val.get('value'), val.get('type'), val.get('datatype') 
        try:
            return data_types.get(val.get('datatype'))(val.get('value')), val.get('type'), val.get('datatype')
        except:
            return None, None, None # in case of mismatch, or unknown data_types

def translateToDict(tuple):
    ret = dict()
    if tuple is None:
        return {'value': ''}
    if tuple[1]:
        ret.update({'type': tuple[1]})
    ret.update({'value': str(tuple[0])})
    if tuple[2]:
        ret.update({'datatype': tuple[2]})
    return ret

class SPARQLTypeError(Exception):
    """Base class for exceptions in this module."""
    pass
