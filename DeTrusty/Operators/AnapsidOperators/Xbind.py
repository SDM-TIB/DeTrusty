from multiprocessing import Queue
from DeTrusty.Sparql.Parser.services import Bind, Expression, Argument
import math
import datetime
import operator


arithmetic_operators = {
    '*': operator.mul,
    '/': operator.truediv,
    '+': operator.add,
    '-': operator.sub,
}

unary_operators = {
    '!': operator.not_,
    'bound': lambda a: len(a) > 0,
    'str': str,
    'floor': math.floor,
    'year': datetime.datetime.year
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
    'positiveInteger': (int, 'numerical')
}

numerical = (int, float)

class Xbind(object):

    name = "BIND"

    def __init__(self, bind):
        self.input = Queue()
        self.qresults = Queue()
        self.bind = bind

    def execute(self, left, dummy, out, processqueue=Queue()):
        self.left = left 
        self.qresults = out
        b_value = self.bind.term
        b_var = self.bind.new_var[1:]
        tuple = self.left.get(True)

        if isinstance(b_value, Argument) or isinstance(b_value, str):

            while (tuple != "EOF"):
                shouldInclude = self.BindTerm_str(tuple)
                if shouldInclude:
                    self.qresults.put(tuple)

                tuple = self.left.get(True)
        
        elif isinstance(b_value, Expression):

            while (tuple != "EOF"):
                res = self.BindTerm_expr(tuple, self.bind.term.op, self.bind.term.left,
                                                        self.bind.term.right)  
                tuple[b_var] = res

                if res:
                    self.qresults.put(tuple)
                   
                tuple = self.left.get(True)

        # Put EOF in queue and exit.
        self.qresults.put("EOF")


    def BindTerm_str(self, tuple):
        isValid = True
        b_var = self.bind.new_var[1:]
        term = self.bind.term
        if isinstance(term, Argument) and (term.name[0] == "\"" or term.name[0] == "\'"):
            b_value = term.name[1:-1]
        else:
            b_value = term
        tuple[b_var] = b_value
        value = tuple[b_var]

        if value != b_value:
            isValid = False

        if isValid:
            return True

        return False          


    def BindTerm_expr(self, tuple, operator, term_left, term_right):
        
        # case 1: Var op NUMBER | Var op Var 
        if isinstance(term_left, Argument) and isinstance(term_right, Argument):
            if term_left.constant:
                res_left = term_left.name
            elif term_left.name.isnumeric() or term_left.name.replace('.','',1).isdigit():
                res_left = term_left.name
            else:
                res_left = self.extractValue(tuple[term_left.name[1:]])
            
            if term_right.constant:
                res_right = term_right.name
            elif term_right.name.isnumeric() or term_right.name.replace('.','',1).isdigit():
                res_right = term_right.name
            else:
                res_right = tuple[term_right.name[1:]]
            
            res = self.evaluateOperator(operator, res_left, res_right)

        # case 2: VAR op Expr | NUMBER op Expr
        elif isinstance(term_left, Argument) and isinstance(term_right, Expression):
   
            if term_left.constant: 
                res_left = term_left.name
            elif term_left.name.isnumeric() or term_left.name.replace('.','',1).isdigit():
                res_left = term_left.name
            else:
                res_left = tuple[term_left.name[1:]]

            res_right = self.extractExpr(tuple, term_right)
            res = self.evaluateOperator(operator, res_left, res_right)

        # case 3: Expr op VAR | Expr op NUMBER
        elif isinstance(term_right, Argument) and isinstance(term_left, Expression):

            if term_right.constant: 
                res_right = term_right.name
            elif term_right.name.isnumeric() or term_right.name.replace('.','',1).isdigit():
                res_right = term_right.name
            else:
                res_right = tuple[term_right.name[1:]]

            if term_left.right is not None:
                res_left = self.extractExpr(tuple, term_left)
                res = self.evaluateOperator(operator, res_left, res_right)
            
            if term_left.right is None:
                left = tuple[term_left.left.name[1:]]
                res_left = self.evaluateUnaryOperator(term_left.op, left)
                res = self.evaluateOperator(operator, res_left, res_right)            
            
        # case 4: unary_operators
        if isinstance(term_left, Argument) and term_right is None:

            if term_left.constant or term_left.name[1:] not in tuple: 
                res_left = term_left.name 
            else:
                res_left = tuple[term_left.name[1:]]
            
            res = self.evaluateUnaryOperator(operator, res_left)

        if isinstance(term_left, Expression) and term_right is None:

            if term_left.constant or term_left.name[1:] not in tuple: 
                res_left = term_left.name 
            else:
                res_left = tuple[term_left.name[1:]]
            
            res = self.evaluateUnaryOperator(operator, res_left)

        # case 5: logical connectives 
        if isinstance(term_left, Expression) and isinstance(term_right, Expression):

            if term_left.right is not None and term_right.right is not None:
                res_left = self.extractExpr(tuple, term_left)
                res_right = self.extractExpr(tuple, term_right)
                res = self.evaluateOperator(operator, res_left, res_right)

            elif term_left.right is None and term_right.right is None:
                left = tuple[term_left.left.name[1:]]
                right = tuple[term_right.left.name[1:]]
                res_left = self.evaluateUnaryOperator(term_left.op, left)
                res_right = self.evaluateUnaryOperator(term_right.op, right)
                res = self.evaluateOperator(operator, res_left, res_right)

        return str(res)


    # For nested_term:
    def extractExpr(self, tuple, nested_term):
        # right_term is Expr
        if isinstance(self.bind.term.right, Expression):
            nested_term_r = self.bind.term.right.right
            nested_term_l = self.bind.term.right.left
            nested_term_o = self.bind.term.right.op
        
        # left_term is Expr
        elif isinstance(self.bind.term.left, Expression):
            nested_term_r = self.bind.term.left.right
            nested_term_l = self.bind.term.left.left
            nested_term_o = self.bind.term.left.op


        # Expr: VAR op (NUMBER op Var) | VAR op (VAR op NUMBER) | FLOAT op (NUMBER op VAR)
        if isinstance(nested_term_l, Argument) and isinstance(nested_term_r, Argument):
            if str(nested_term_l).isnumeric() or str(nested_term_l).replace('.','',1).isdigit():
                if nested_term_r.constant:
                    res_right = nested_term_r.name
                else:
                    res_right = tuple[nested_term_r.name[1:]]
                
                res = self.evaluateOperator(nested_term_o, nested_term_l, res_right)
            
            elif str(nested_term_r).isnumeric() or str(nested_term_r).replace('.','',1).isdigit():
                if nested_term_l.constant:
                    res_left = nested_term_l.name
                else:
                    res_left = tuple[nested_term_l.name[1:]]
                
                res = self.evaluateOperator(nested_term_o, res_left, nested_term_r)

        # Expr: NUMBER op (NUMBER op VAR) 
        if isinstance(nested_term_l, str) and isinstance(nested_term_r, Argument):
            if nested_term_r.constant:
                res_right = nested_term_r.name
            else:
                res_right = tuple[nested_term_r.name[1:]]

            res = self.evaluateOperator(nested_term_o, nested_term_l, res_right)

        # Expr: NUMBER op (VAR op NUMBER)
        if isinstance(nested_term_l, Argument) and isinstance(nested_term_r, str):
            if nested_term_l.constant:
                res_left = nested_term_l.name
            else:
                res_left = tuple[nested_term_l.name[1:]] 

            res = self.evaluateOperator(nested_term_o, res_left, nested_term_r)           
            
        return res

    
    def evaluateOperator(self, operator, term_left, term_right):
        if operator in arithmetic_operators:
            return self.evaluateAritmethic(operator, term_left, term_right)
        elif (operator in unary_operators):
            return self.evaluateUnaryOperator(operator, term_left)
        elif (operator in test_operators):
            return self.evaluateTest(operator, term_left, term_right)
        elif (operator in logical_connectives):
            return self.evaluateLogicalConnective(operator, term_left, term_right)
            

    def evaluateAritmethic(self, operator, term_left, term_right):
        term_left = str(term_left)
        term_right = str(term_right)

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


    def evaluateUnaryOperator(self, operator, term_left):

        if (operator.lower() == 'floor'):
            return (unary_operators[operator.lower()](math.floor(float(term_left))),int)

        elif (operator.lower() == 'str'):
            return (unary_operators[operator.lower()](str(term_left)), str)

        elif (operator.lower() == 'bound'):
            if term_left[0] != "?":
                return (unary_operators[operator.lower()](term_left), bool)
            elif term_left[0] == "?":
                return (False, bool)

        elif (operator.lower() == 'year'):
            
            for format in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%SZ", "%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%d"):
                try:
                    term_left = str(term_left)
                    date = datetime.datetime.strptime(term_left, format)
                    return int(date.year)
                    
                except ValueError:
                    pass
                
            raise ValueError("no valid date format found")

        else:
            raise SPARQLTypeError


    def evaluateTest(self, operator, left, right):

        if left and right:
            (term_left, type_left) = left, type(left)
            (term_right, type_right) = right, type(right)
            term_left = str(term_left)
            term_right = str(term_right)
        else:
            print("Exception: left or right operand None.", left, right)
            raise Exception

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


    def evaluateLogicalConnective(self, operator, term_left, term_right):
        
        (isEBV_left, ebv_left) = self.evaluateEBV(term_left)
        (isEBV_right, ebv_right) = self.evaluateEBV(term_right)

        if (isEBV_left and isEBV_right):
            return (logical_connectives[operator](ebv_left, ebv_right), bool)

        elif (isEBV_left):
            res = logical_connectives[operator](ebv_left, 'Error')
            if (res == 'Error'):
                raise SPARQLTypeError
            else:
                return (res, bool)

        elif (isEBV_right):
            res = logical_connectives[operator](ebv_right, 'Error')
            if (res == 'Error'):
                raise SPARQLTypeError
            else:
                return (res, bool)

    '''
    evaluateEBV: calculates whether an argument is an Effective Boolean Value (EBV)
                 according to the definition in the SPARQL documentation 
                 See: http://www.w3.org/TR/sparql11-query/#ebv

    input: val -- an argument
    return: (isEBV, EBV) -- both of Python type bool
    you still need to make it consistent with XFilter

    '''

    def evaluateEBV(self, value):
        (casted_val, type_val) = value

        # Handles python data types.
        if (isinstance(casted_val, bool)):
            return (True, casted_val)

        # Rule 1
        if ((type_val == bool) and (casted_val != 'True') and (casted_val != 'False')):
            return (True, False)

        # Rule 2
        if (type_val == bool):
            if (casted_val == 'True'):
                return (True, True)
            elif (casted_val == 'False'):
                return (True, False)

        # Rule 3: !Bound
        if (type_val == str):
            if casted_val[0] == "?":
                return (True, False)
            elif casted_val.isnumeric():
                return (True, True)

        # Rule 4: The error type should be raised by the evaluators.
        return (False, None)


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


class SPARQLTypeError(Exception):
    """Base class for exceptions in this module."""
    pass