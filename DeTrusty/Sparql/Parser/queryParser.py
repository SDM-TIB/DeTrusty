import urllib.parse
from ply import lex, yacc
import sys
# not all module needed (TODO: check after integrating expression to Having, Aggregate)
from .services import Query, Argument, Triple, UnionBlock, JoinBlock, Optional, Filter, Expression, Values, Bind, Aggregate, Having, HavingHelper, Service

test = list()

# Lexer
reserved = {
    'PREFIX': 'PREFIX',
    'UNION': 'UNION',
    'FILTER': 'FILTER',
    'OPTIONAL': 'OPTIONAL',
    
    'VALUES' : 'VALUES',
    'UNDEF' : 'UNDEF',

    'BIND': 'BIND',
    'AS': 'AS',
    'SERVICE': 'SERVICE',
    'SELECT': 'SELECT',
    'DISTINCT': 'DISTINCT',
    'WHERE': 'WHERE',
    'LIMIT': 'LIMIT',
    'OFFSET': 'OFFSET',
    'ORDER': 'ORDER',
    'BY': 'BY',
    'DESC': 'DESC',
    'ASC': 'ASC',
    'IN' : 'IN',
    'NOT' : 'NOT',
    'FALSE': 'FALSE',
    'TRUE': 'TRUE',
    'GROUP': 'GROUP',
    'COUNT': 'COUNT',
    'SUM': 'SUM',
    'AVG': 'AVG',
    'MIN': 'MIN',
    'MAX': 'MAX',
    'SAMPLE': 'SAMPLE',
    'GROUP_CONCAT': 'GROUP_CONCAT',
    'SEPARATOR': 'SEPARATOR',
    'HAVING': 'HAVING',
    'BOUND': 'BOUND',
    'REGEX': 'REGEX',
    'ISIRI': 'ISIRI',
    'ISURI': 'ISURI',
    'ISBLANK': 'ISBLANK',
    'ISLITERAL': 'ISLITERAL',
    'IRI': 'IRI',
    'ABS': 'ABS',
    'CEIL': 'CEIL',
    'LANG': 'LANG',
    'ROUND': 'ROUND',
    'STRLEN': 'STRLEN',
    'FLOOR': 'FLOOR',
    'DATATYPE': 'DATATYPE',
    'SAMETERM': 'SAMETERM',
    'LANGMATCHES': 'LANGMATCHES',
    'STR': 'STR',
    'UCASE': 'UCASE',
    'LCASE': 'LCASE',
    'ENCODE_FOR_URI': 'ENCODE_FOR_URI',
    'YEAR': 'YEAR',
    'MONTH': 'MONTH',
    'DAY': 'DAY',
    'HOURS': 'HOURS',
    'MINUTES': 'MINUTES',
    'SECONDS': 'SECONDS',
    'CONTAINS': 'CONTAINS',
    'STRSTARTS': 'STRSTARTS',
    'STRENDS': 'STRENDS',
    'STRBEFORE': 'STRBEFORE',
    'STRAFTER': 'STRAFTER',
    'STRLANG': 'STRLANG',
    'STRDT': 'STRDT',
    'SUBSTR': 'SUBSTR',
    'TIMEZONE': 'TIMEZONE',
    'TZ': 'TZ',
    'CONCAT': 'CONCAT',
    'REPLACE': 'REPLACE',
    'EXIST': 'EXIST',
    'MD5': 'MD5',
    'COALESCE': 'COALESCE',
    'IF': 'IF',
    'SHA1': 'SHA1',
    'SHA256': 'SHA256',
    'SHA384': 'SHA384',
    'SHA512': 'SHA512',
    'ISNUMERIC': 'ISNUMERIC',
    'RAND': 'RAND',
    'NOW': 'NOW',
    'UUID': 'UUID',
    'STRUUID': 'STRUUID',
    'BNODE': 'BNODE'
}


tokens = [
    # "RDFTYPE",
    "CONSTANT",
    "URI",
    "NUMBER",
    "VARIABLE",
    "LKEY",
    "RKEY",
    "COLON",
    "SEMICOLON",
    "POINT",
    "COMA",
    "LPAR",
    "RPAR",
    "ID",
    "NIL",
    "EQUALS",
    "NEQUALS",
    "LESS",
    "LESSEQ",
    "GREATER",
    "GREATEREQ",
    "NEG",
    "AND",
    "OR",
    "ALL",
    "PLUS",
    "MINUS",
    "DIV",
    "DOUBLE",
    "INTEGER",
    "DECIMAL",
    "FLOAT",
    "STRING",
    "BOOLEAN",
    "DATETIME",
    "NONPOSINT",
    "NEGATIVEINT",
    "LONG",
    "INT",
    "SHORT",
    "BYTE",
    "NONNEGINT",
    "UNSIGNEDLONG",
    "UNSIGNEDINT",
    "UNSIGNEDSHORT",
    "UNSIGNEDBYTE",
    "POSITIVEINT"
    ] + list(reserved.values())

# t_RDFTYPE = r"a"


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9\-]*'
    # print t
    t.type = reserved.get(t.value.upper(), 'ID')    # Check for reserved words
    return t


t_CONSTANT = r"(\"|\')[^\"\'\n\r]*(\"|\')((@[a-z][a-z]) | (\^\^[<](https?|ftp|file)://[-a-zA-Z0-9+&@#/%?=~_|!:,.;]*[-a-zA-Z0-9+&@#/%=~_|][>]))?" # [<]http[://]+www[.]w3[.]org[/]2001[/]XMLSchema[#]\w+
t_URI = r"<\S+>"
t_NUMBER = r"([0-9])+"
t_VARIABLE = r"([\?]|[\$])([A-Z]|[a-z])\w*"
t_LKEY = r"\{"
t_LPAR = r"\("
t_RPAR = r"\)"
t_COLON = r"\:"
t_SEMICOLON = r";"
# t_RDFTYPE = r"a"
# t_RKEY = r"(\.)?\}"
t_RKEY = r"(\.)?\s*\}"
t_POINT = r"\."
t_COMA = r"\,"

t_EQUALS = r"="
t_NEQUALS = r"\!="
t_LESS = r"<"
t_LESSEQ = r"<="
t_GREATER = r">"
t_GREATEREQ = r">="
t_NEG  =  r"\!"
t_AND = r"\&\&"
t_OR = r"\|\|"
# t_NIL =

t_ALL = r"[*]"
t_PLUS = r"\+"
t_MINUS = r"\-"
t_DIV = r"/"

t_DOUBLE = r"xsd\:double"
t_INTEGER = r"xsd\:integer"
t_DECIMAL = r"xsd\:decimal"
t_FLOAT = r"xsd\:float"
t_STRING = r"xsd\:string"
t_BOOLEAN = r"xsd\:boolean"
t_DATETIME = r"xsd\:dateTime"
t_NONPOSINT = r"xsd\:nonPositiveInteger"
t_NEGATIVEINT = r"xsd\:negativeInteger"
t_LONG = r"xsd\:long"
t_INT = r"xsd\:int"
t_SHORT = r"xsd\:short"
t_BYTE = r"xsd\:byte"
t_NONNEGINT = r"xsd\:nonNegativeInteger"
t_UNSIGNEDLONG = r"xsd\:unsignedLong"
t_UNSIGNEDINT = r"xsd\:unsignedInt"
t_UNSIGNEDSHORT = r"xsd\:unsignedShort"
t_UNSIGNEDBYTE = r"xsd\:unsignedByte"
t_POSITIVEINT = r"xsd\:positiveInteger"

t_ignore = ' \t\n'

xsd = "http://www.w3.org/2001/XMLSchema#"


def t_error(t):
    raise TypeError("Unknown text '%s' in line %d " % (t.value, t.lexer.lineno, ))


# Define a rule so we can track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


lexer = lex.lex()


# Parser


def p_parse_sparql_0(p):
    """
    parse_sparql : prefix_list query group_by having_clause order_by limit offset
    """
    (vs, ts, d) = p[2]
    p[0] = Query(prefs=p[1], args=vs, body=ts, distinct=d, group_by=p[3], order_by=p[5], limit=p[6], offset=p[7], having=p[4])


def p_parse_sparql_1(p):
    """
    parse_sparql : empty
    """
    p[0] = None


def p_empty(p):
    """
    empty :
    """
    pass


# in Specification PREFIX : <http://example.com/> (without ID) is a valid declaration, here not

def p_prefix_list(p):
    """
    prefix_list : prefix prefix_list
    """
    p[0] = [p[1]] + p[2]


def p_empty_prefix_list(p):
    """
    prefix_list : empty
    """
    p[0] = []


def p_prefix(p):
    """
    prefix : PREFIX uri
    """
    p[0] = p[2]


def p_uri_0(p):
    """
    uri : ID COLON ID
    """
    p[0] = p[1] + p[2] + p[3]

def p_uri_1(p):
    """
    uri : ID COLON URI
    """
    p[0] = p[1] + p[2] + p[3]


def p_uri_2(p):
    """
    uri : URI
    """
    p[0] = p[1]


def p_uri_3(p):
    """
    uri : ID COLON YEAR
    """
    p[0] = p[1] + p[2] + p[3]

def p_uri_4(p):
    """
    uri : ID COLON ID NUMBER
    """
    p[0] = p[1] + p[2] + p[3] + p[4]

def p_uri_5(p):
    """
    uri : ID COLON NUMBER
    """
    p[0] = p[1] + p[2] + p[3]

########################################################################

# REDUCED not yet implemented, necessary?

def p_query_0(p):
    """
    query : SELECT distinct var_list WHERE LKEY group_graph_pattern RKEY
    """
    p[0] = (p[3], p[6], p[2])


def p_query_1(p):
    """
    query : SELECT distinct ALL WHERE LKEY group_graph_pattern RKEY
    """
    p[0] = ([], p[6], p[2])


def p_distinct_0(p):
    """
    distinct : DISTINCT
    """
    p[0] = True


def p_distinct_1(p):
    """
    distinct : empty
    """
    p[0] = False


def p_single_var_list_0(p): 
    """
    var_list : VARIABLE
    """
    # if p[1][1:] not in test:
    #     p_error(p[1])
        # print('grouping variable should be in aggregate')
        # sys.exit()
    p[0] = [Argument(p[1], False)]


def p_single_var_list_1(p): 
    """
    var_list : LPAR expression AS VARIABLE RPAR
    """
    p[2].alias = p[4]
    p[0] = [p[2]]


# def p_single_var_list_2(p): 
    # """
    # var_list : VARIABLE AS VARIABLE
    # """
    # p[0] = [Argument(p[1], False, alias=p[3])]


def p_var_list_0(p):
    """
    var_list : VARIABLE var_list 
    """
    # if p[1][1:] not in test:
    #     p_error(p[1])
        # print('grouping variable should be in aggregate')
        # sys.exit()
    p[0] = [Argument(p[1], False)] + p[2]


def p_var_list_1(p):
    """
    var_list : LPAR expression AS VARIABLE RPAR var_list 
    """
    p[2].alias = p[4]
    p[0] = [p[2]] + p[6]


# def p_var_list_2(p):
    # """
    # var_list : VARIABLE AS VARIABLE var_list
    # """
    # p[0] = [Argument(p[1], False, alias=p[3])] + p[4]


################################################################
# TODO: Adjust until Xgroupby.py                               #
################################################################


def p_group_by_0(p):
   """
   group_by : GROUP BY group_var group_var_list
   """
   test.append(p[3].name[1:])
   p[0] = [p[3]] + p[4]


def p_group_by_1(p):
   """
   group_by : empty
   """
   p[0] = []


def p_group_var_0(p):                          
   """                                        
   group_var : VARIABLE                        
   """
   p[0] = Argument(p[1], False)


def p_group_var_1(p):                          
   """                                        
   group_var : LPAR expression AS VARIABLE RPAR                         
   """
   p[0] = Argument(p[2], False, alias=p[4])


def p_group_var_2(p):                          
   """                                        
   group_var : LPAR expression RPAR                         
   """
   p[0] = Argument(p[1], False)


def p_group_var_3(p):                          
   """                                        
   group_var : built_in_call
   """
   p[0] = Argument(p[1], False)


def p_group_var_list_0(p):
   """
   group_var_list : group_var group_var_list
   """
   p[0] = [p[1]] + p[2]


def p_group_var_list_1(p):
   """
   group_var_list : empty
   """
   p[0] = []



########################### TODO #############################################
# -> Adjust the orderby module & services.py (for multiple condition)        #
##############################################################################


def p_order_by_0(p):
    """
    order_by : ORDER BY order_by_condition
    """
    p[0] = p[3]


def p_order_by_1(p):
    """
    order_by : empty
    """
    p[0] = []


def p_order_by_condition_0(p):
    """
    order_by_condition : ASC constraint order_by_condition 
    """
    p[0] = [Argument(p[2], desc=False)] + p[3]


def p_order_by_condition_1(p):
    """
    order_by_condition : DESC constraint order_by_condition
    """
    p[0] = [Argument(p[2], desc=True)] + p[3]
    

def p_order_by_condition_2(p):
    """
    order_by_condition : constraint order_by_condition
    """
    p[0] =  [Argument(p[1], desc=False)] + p[2] # by default ASC


def p_order_by_condition_3(p):
    """
    order_by_condition : ASC VARIABLE order_by_condition
    """
    p[0] =  [Argument(p[2], desc=False)] + p[3]


def p_order_by_condition_4(p):
    """
    order_by_condition : DESC VARIABLE order_by_condition
    """
    p[0] =  [Argument(p[2], desc=True)] + p[3]


def p_order_by_condition_5(p):
    """
    order_by_condition : VARIABLE 
    """
    p[0] =  [Argument(p[1], desc=True)]


############################################################
# -> Constraint does not include FunctionCall from spec.   #
############################################################


def p_constraint_0(p):
    """
    constraint : bracketted_expression 
    """
    p[0] = p[1]


def p_constraint_1(p):
    """
    constraint : built_in_call 
    """
    p[0] = p[1]


############################################################


def p_limit_0(p):
    """
    limit : LIMIT NUMBER
    """
    p[0] = p[2]


def p_limit_1(p):
    """
    limit : empty
    """
    p[0] = -1


def p_offset_0(p):
    """
    offset : OFFSET NUMBER
    """
    p[0] = p[2]


def p_offset_1(p):
    """
    offset : empty
    """
    p[0] = -1


######################### TODO #############################
# -> Multiple constrain ?                                  #
# -> fix until Xhaving.py                                  #
############################################################


def p_having_clause_0(p):
    """
    having_clause : empty
    """
    p[0] = None


def p_having_clause_1(p):
    """
    having_clause : HAVING constraint
    """
    p[0] = p[1]


############################################################
# this section to be re-checked, TODO: restructure ?


def p_ggp_0(p):
    """
    group_graph_pattern : union_block
    """
    p[0] = UnionBlock(p[1])


def p_union_block_0(p):
    """
    union_block : pjoin_block rest_union_block POINT pjoin_block
    """
    punion = [JoinBlock(p[1])] + p[2]
    pjoin = [UnionBlock(punion)] + p[4]
    p[0] = [JoinBlock(pjoin)]


def p_union_block_1(p):
    """
    union_block : pjoin_block rest_union_block pjoin_block
    """
    punion = [JoinBlock(p[1])] + p[2]
    if p[3] != []:
        pjoin = [UnionBlock(punion)] + p[3]
        p[0] = [JoinBlock(pjoin)]
    else:
        p[0] = [JoinBlock(p[1])] + p[2]


def p_union_block_2(p):
    """
    union_block : pjoin_block rest_union_block
    """
    p[0] = [JoinBlock(p[1])] + p[2]


def p_ppjoin_block_0(p):
    """
    pjoin_block : LKEY join_block RKEY
    """
    p[0] = p[2]


def p_ppjoin_block_1(p):
    """
    pjoin_block : join_block
    """
    p[0] = p[1]


def p_ppjoin_block_2(p):
    """
    pjoin_block : empty
    """
    p[0] = []


def p_join_block_0(p):
    """
    join_block : LKEY union_block RKEY rest_join_block
    """
    if p[4] != [] and isinstance(p[4][0], Filter):
        p[0] = [UnionBlock(p[2])] + p[4]
    if p[4] != [] and isinstance(p[4][0], Values):
        p[0] = [UnionBlock(p[2])] + p[4]
    elif p[4] != []:
        p[0] = [UnionBlock(p[2])] + [JoinBlock(p[4])]
    else:
        p[0] = [UnionBlock(p[2])]


def p_join_block_1(p):
    """
    join_block : bgp rest_join_block
    """
    p[0] = [p[1]] + p[2]


def p_rest_join_block_0(p):
    """
    rest_join_block : empty
    """
    p[0] = []


def p_rest_join_block_1(p):
    """
    rest_join_block : POINT bgp rest_join_block
    """
    p[0] = [p[2]] + p[3]


def p_rest_join_block_2(p):
    """
    rest_join_block : bgp rest_join_block
    """
    p[0] = [p[1]] + p[2]


def p_rest_union_block_0(p):
    """
    rest_union_block : empty
    """
    p[0] = []


def p_rest_union_block_1(p):
    """
    rest_union_block : UNION LKEY join_block rest_union_block RKEY rest_union_block
    """
    p[0] = [JoinBlock(p[3])] + p[4] + p[6]


def p_service(p):
    """
    service : SERVICE uri LKEY group_graph_pattern_service RKEY
    """
    p[0] = Service(p[2], p[4])


def p_ggp_service_0(p):
    """
    group_graph_pattern_service : union_block_service
    """
    p[0] = UnionBlock(p[1])


def p_union_block_service_0(p):
    """
    union_block_service : join_block_service rest_union_block_service
    """
    p[0] = [JoinBlock(p[1])] + p[2]


def p_rest_union_block_service_0(p):
    """
    rest_union_block_service : empty
    """
    p[0] = []


def p_rest_union_block_service_1(p):
    """
    rest_union_block_service : UNION LKEY join_block_service rest_union_block_service RKEY rest_union_block_service
    """
    p[0] = [JoinBlock(p[3])] + p[4] + p[6]


def p_join_block_service_0(p):
    """
    join_block_service : LKEY bgp_service rest_join_block_service RKEY rest_join_block_service
    """
    jb_list = [p[2]] + p[3]
    if p[5] != [] and isinstance(p[5][0], Filter):
        p[0] = [UnionBlock([JoinBlock(jb_list)])] + p[5]
    elif isinstance(p[2], UnionBlock):
        p[0] = [p[2]] + p[3] + p[5]
    else:
        p[0] = [UnionBlock([JoinBlock(jb_list)])] + p[5]


def p_join_block_service_1(p):
    """
    join_block_service : bgp_service rest_join_block_service
    """
    p[0] = [p[1]] + p[2]


def p_rest_join_block_service_0(p):
    """
    rest_join_block_service : empty
    """
    p[0] = []


def p_rest_join_block_service_1(p):
    """
    rest_join_block_service : POINT bgp_service rest_join_block_service
    """
    p[0] = [p[2]] + p[3]


def p_rest_join_block_service_2(p):
    """
    rest_join_block_service : bgp_service rest_join_block_service
    """
    p[0] = [p[1]] + p[2]


def p_bgp_0(p):
    """
    bgp :  LKEY bgp UNION bgp rest_union_block RKEY
    """
    ggp = [JoinBlock([p[2]])] + [JoinBlock([p[4]])] + p[5]
    p[0] = UnionBlock(ggp)


def p_bgp_01(p):
    """
    bgp : bgp UNION bgp rest_union_block
    """
    ggp = [JoinBlock([p[1]])] + [JoinBlock([p[3]])] + p[4]
    p[0] = UnionBlock(ggp)


def p_bgp_1(p):
    """
    bgp : triple
    """
    p[0] = p[1]

# Filter ::=  'FILTER' Constraint (doesn't include FunctionCall yet)
def p_bgp_2(p):
    """
    bgp : FILTER LPAR expression RPAR
    """
    p[0] = Filter(p[3])


def p_bgp_3(p):
    """
    bgp : FILTER relational_expression
    """
    p[0] = Filter(p[2])


def p_bgp_4(p):
    """
    bgp : OPTIONAL LKEY group_graph_pattern RKEY
    """
    p[0] = Optional(p[3])


#def p_bgp_5(p):
#    """
#    bgp : LKEY join_block rest_union_block RKEY
#    """
#    bgp_arg = p[2] + p[3]
#    p[0] = UnionBlock(JoinBlock(bgp_arg))


def p_bgp_6(p):
    """
    bgp : LKEY join_block RKEY
    """
    if len(p[2]) == 1:
        p[0] = p[2][0]
    else:
        p[0] = JoinBlock(p[2])


#####################################################################
# TODO: throw unmatched variable length exception like in Virtuoso 


def p_bgp_7(p):
    """
    bgp : VALUES VARIABLE LKEY data_block_value RKEY
    """
    p[0] = Values([Argument(p[2])], p[4], 'single')


def p_bgp_8(p):
    """
    bgp : VALUES LPAR value_vars RPAR LKEY data_block_multiple_value RKEY
    """
    p[0] = Values(p[3], p[6])


def p_value_vars_0(p):
    """
    value_vars : empty
    """
    p[0] = []


def p_value_vars_1(p):
    """
    value_vars : VARIABLE value_vars
    """
    p[0] = [Argument(p[1])] + p[2]


def p_data_block_value_0(p):
    """
    data_block_value : empty
    """
    p[0] = []


def p_data_block_value_1(p):
    """
    data_block_value : rdf_literal data_block_value 
                     | numeric_literal data_block_value 
                     | boolean_literal data_block_value 
    """
    p[0] = [p[1]] + p[2]


def p_data_block_value_2(p):
    """
    data_block_value : UNDEF data_block_value
                     | uri data_block_value
    """
    p[0] = [Argument(p[1])] + p[2]


def p_data_block_multiple_value_0(p):
    """
    data_block_multiple_value : empty
    """
    p[0] = []


def p_data_block_multiple_value_1(p):
    """
    data_block_multiple_value : LPAR data_block_value RPAR data_block_multiple_value
    """
    p[0] = [p[2]] + p[4]

#####################################################################


def p_bgp_9(p):
    """
    bgp : BIND LPAR expression AS VARIABLE RPAR
    """
    p[0] = Bind(p[3], p[5])


def p_bgp_10(p):
    """
    bgp : service
    """
    p[0] = ([p[1]], [])


def p_bgp_11(p):
    """
    bgp : LKEY service RKEY
    """
    p[0] = ([p[2]], [])


def p_bgp_service_01(p):
    """
    bgp_service :  LKEY join_block_service UNION join_block_service rest_union_block_service RKEY
    """
    ggp = [JoinBlock(p[2])] + [JoinBlock(p[4])] + p[5]
    p[0] = UnionBlock(ggp)


def p_bgp_service_02(p):
    """
    bgp_service :  join_block_service UNION join_block_service rest_union_block_service
    """
    ggp = [JoinBlock(p[1])] + [JoinBlock(p[3])] + p[4]
    p[0] = UnionBlock(ggp)


def p_bgp_service_1(p):
    """
    bgp_service : triple
    """
    p[0] = p[1]


def p_bgp_service_2(p):
    """
    bgp_service : FILTER LPAR expression RPAR
    """
    p[0] = Filter(p[3])


def p_bgp_service_3(p):
    """
    bgp_service : FILTER relational_expression
    """
    p[0] = Filter(p[2])


def p_bgp_service_4(p):
    """
    bgp_service : OPTIONAL LKEY group_graph_pattern_service RKEY
    """
    p[0] = Optional(p[3])


def p_bgp_service_5(p):
    """
    bgp_service : LKEY join_block_service rest_union_block_service RKEY
    """
    bgp_arg = p[2] + p[3]
    p[0] = UnionBlock(JoinBlock(bgp_arg))


#############################################################################
# TODO: Test and adjust                                                     #
#############################################################################


def p_expression(p):
    """
    expression : conditional_or_expression
    """
    p[0] = p[1]


def p_conditional_or_expression(p):
    """
    conditional_or_expression : conditional_and_expression or_expr
    """
    if p[2] is not None:
        p[0] = Expression('||', p[1], p[2], 'logical')
    else:
        p[0] = p[1]


def p_or_expr_0(p):
    """
    or_expr : OR conditional_and_expression or_expr
    """
    if p[3] is not None:
        p[0] = Expression(p[1], p[2], p[3], 'logical')
    else:
        p[0] = p[2]


def p_or_expr_1(p):
    """
    or_expr : empty
    """
    p[0] = None


def p_conditional_and_expression(p):
    """
    conditional_and_expression : relational_expression and_expr
    """
    if p[2] is not None:
        p[0] = Expression('&&', p[1], p[2], 'logical')
    else:
        p[0] = p[1]


def p_and_expr_0(p):
    """
    and_expr : AND relational_expression and_expr
    """
    if p[3] is not None:
        p[0] = Expression(p[1], p[2], p[3], 'logical')
    else:
        p[0] = p[2]


def p_and_expr_1(p):
    """
    and_expr : empty
    """
    p[0] = None


def p_relational_expression_0(p):
    """
    relational_expression : numeric_expression EQUALS numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_1(p):
    """
    relational_expression : numeric_expression NEQUALS numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_2(p):
    """
    relational_expression : numeric_expression LESS numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_3(p):
    """
    relational_expression : numeric_expression GREATER numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_4(p):
    """
    relational_expression : numeric_expression LESSEQ numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_5(p):
    """
    relational_expression : numeric_expression GREATEREQ numeric_expression
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational')


def p_relational_expression_6(p):
    """
    relational_expression : numeric_expression IN expression_list
    """
    p[0] = Expression(p[2], p[1], p[3], 'relational') 


def p_relational_expression_7(p):
    """
    relational_expression : numeric_expression NOT IN expression_list
    """
    inner_exp = Expression(p[3], p[1], p[4], 'relational')
    p[0] = Expression('!', inner_exp, exp_type = 'unary')


def p_relational_expression_8(p):
    """
    relational_expression : numeric_expression
    """
    p[0] = p[1]


def p_expression_list_0(p):
    """
    expression_list : LPAR expression RPAR
    """
    p[0] = [p[2]]


def p_expression_list_1(p):
    """
    expression_list : LPAR expression next_expr RPAR
    """
    p[0] = [p[2]] + p[3]


def p_next_expr_0(p):
    """
    next_expr : COMA expression next_expr
    """
    p[0] = [p[2]] + p[3]


def p_next_expr_1(p):
    """
    next_expr : empty
    """
    p[0] = []


def p_numeric_expression(p):
    """
    numeric_expression : additive_expression
    """
    p[0] = p[1]


def p_additive_expression(p):
    """
    additive_expression : multiplicative_expression arith_op
    """
    if p[2] != None:
        op, right = p[2]
        p[0] = Expression(op, p[1], right, 'arithmetic')
    else:
        p[0] = p[1]


def p_arith_op_0(p):
    """
    arith_op : plus_or_minus
    """
    p[0] = p[1]


def p_arith_op_1(p):
    """
    arith_op : empty
    """
    p[0] = None


def p_plus_or_minus(p):
    """
    plus_or_minus : PLUS multiplicative_expression arith_op
                   | MINUS multiplicative_expression arith_op
    """
    if p[3] != None:
        op, right = p[3]
        p[0] = p[1], Expression(op, p[2], right, 'arithmetic')
    else:
        p[0] = p[1], p[2]


def p_multiplicative_expression(p):
    """
    multiplicative_expression : unary_expression mult_div_unary
    """
    if p[2] is not None:
        op, right = p[2]
        p[0] = Expression(op, p[1], right, 'arithmetic')
    else:
        p[0] = p[1]


def p_mult_div_unary_0(p):
    """
    mult_div_unary : ALL unary_expression mult_div_unary
    """
    if p[3] != None:
        op, right = p[3]
        p[0] = p[1], Expression(op, p[2], right, 'arithmetic')
    else:
        p[0] = p[1], p[2]


def p_mult_div_unary_1(p):
    """
    mult_div_unary : DIV unary_expression mult_div_unary
    """
    if p[3] != None:
        op, right = p[3]
        p[0] = p[1], Expression(op, p[2], right, 'arithmetic')
    else:
        p[0] = p[1], p[2]


def p_mult_div_unary_2(p):
    """
    mult_div_unary : empty
    """
    p[0] = None


def p_unary_expression_0(p):
    """
    unary_expression : primary_expression
    """
    p[0] = p[1]


def p_unary_expression_1(p):
    """
    unary_expression : NEG primary_expression
                      | PLUS primary_expression
                      | MINUS primary_expression
    """
    p[0] = Expression(p[1], p[2], None, 'unary')


def p_primary_expression_0(p):
    """
    primary_expression : VARIABLE
    """
    p[0] = Argument(p[1], False)


def p_primary_expression_1(p):
    """
     primary_expression :  	bracketted_expression
                            | iri_or_function
                            | built_in_call
                            | rdf_literal
                            | numeric_literal
                            | boolean_literal
    """
    p[0] = p[1]


def p_bracketted_expression(p):
    """
    bracketted_expression : LPAR expression RPAR
    """
    p[0] = p[2]


# TODO: this is not implemented correctly yet, e.g. ID translation, etc. so the input must be URI
def p_iri_or_function_0(p):
    """
    iri_or_function : uri
    """
    p[0] = Argument(p[1], True)


# TODO: follow the spec. This is hardly simplified
def p_iri_or_function_1(p):
    """
    iri_or_function : type_casting VARIABLE
    """
    p[0] = Expression(p[1], Argument(p[2], False))


# TODO: follow the spec. This is hardly simplified
def p_iri_or_function_2(p):
    """
    iri_or_function : type_casting CONSTANT
    """
    p[0] = Expression(p[1], Argument(p[2], True))


# TODO: supposed to be uri and not constrained to the type_casting
def p_type_casting_0(p):
    """
    type_casting : DOUBLE 
                  | INTEGER
                  | DECIMAL
                  | FLOAT
                  | STRING
                  | BOOLEAN
                  | DATETIME
                  | NONPOSINT
                  | NEGATIVEINT
                  | LONG
                  | INT
                  | SHORT
                  | BYTE
                  | NONNEGINT
                  | UNSIGNEDLONG
                  | UNSIGNEDINT
                  | UNSIGNEDSHORT
                  | UNSIGNEDBYTE
                  | POSITIVEINT
    """
    p[0] = p[1]


# TODO: check whether the terminal from CONSTANT correct or not and test
def p_rdf_literal(p):
    """
    rdf_literal : CONSTANT
    """
    c = p[1].strip()
    if "@" in p[1]:
        p[0] = Argument(c[:c.find("^")], True, datatype="<" + xsd + "string>", lang=c[c.rfind("@")+1:], gen_type = str)
    elif xsd in p[1]:
        p[0] = Argument(c[:c.find("^")], True, datatype=c[c.rfind("^")+1:], gen_type = None)
    else:
        p[0] = Argument(p[1], True)


def p_numeric_literal_0(p):
   """
   numeric_literal : NUMBER
   """
   p[0] = Argument(p[1], True)


def p_numeric_literal_1(p):
   """
   numeric_literal : NUMBER POINT NUMBER
   """
   decimalNumber = str(p[1]) + p[2] + str(p[3])
   p[0] = Argument(decimalNumber, True)


# TODO: add double (with EXPONENT token)


def p_boolean_literal(p):
   """
   boolean_literal : TRUE
                    | FALSE
   """
   p[0] = Argument(p[1], True, datatype = xsd + 'boolean', gen_type = bool)


# TODO: builtInCall need to be rechecked, and developing new strategy, so that it won't take too much comparison during execution
def p_built_in_call_0(p):
    """
     built_in_call : STR LPAR expression RPAR
                    | LANG LPAR expression RPAR
                    | DATATYPE LPAR expression RPAR
                    | IRI LPAR expression RPAR
                    | URI LPAR expression RPAR
                    | ABS LPAR expression RPAR
                    | CEIL LPAR expression RPAR
                    | FLOOR LPAR expression RPAR
                    | ROUND LPAR expression RPAR
                    | STRLEN LPAR expression RPAR
                    | UCASE LPAR expression RPAR
                    | LCASE LPAR expression RPAR
                    | ENCODE_FOR_URI LPAR expression RPAR
                    | YEAR LPAR expression RPAR
                    | MONTH LPAR expression RPAR
                    | DAY LPAR expression RPAR
                    | HOURS LPAR expression RPAR
                    | MINUTES LPAR expression RPAR
                    | SECONDS LPAR expression RPAR
                    | TIMEZONE LPAR expression RPAR
                    | TZ LPAR expression RPAR
                    | MD5 LPAR expression RPAR
                    | SHA1 LPAR expression RPAR
                    | SHA256 LPAR expression RPAR
                    | SHA384 LPAR expression RPAR
                    | SHA512 LPAR expression RPAR
                    | ISIRI LPAR expression RPAR
                    | ISURI LPAR expression RPAR
                    | ISBLANK LPAR expression RPAR
                    | ISLITERAL LPAR expression RPAR
                    | ISNUMERIC LPAR expression RPAR
                    | BNODE LPAR expression RPAR
    """
    p[0] = Expression(p[1], p[3], exp_type = 'builtInUnary')


def p_built_in_call_1(p):
    """
     built_in_call : LANGMATCHES LPAR expression COMA expression RPAR
                    | CONTAINS LPAR expression COMA expression RPAR
                    | STRSTARTS LPAR expression COMA expression RPAR
                    | STRENDS LPAR expression COMA expression RPAR
                    | STRBEFORE LPAR expression COMA expression RPAR
                    | STRAFTER LPAR expression COMA expression RPAR
                    | STRLANG LPAR expression COMA expression RPAR
                    | STRDT LPAR expression COMA expression RPAR
                    | SAMETERM LPAR expression COMA expression RPAR
                    | REGEX LPAR expression COMA expression RPAR
                    | SUBSTR LPAR expression COMA expression RPAR
    """
    p[0] = Expression(p[1], p[3], p[5], 'builtInBinary')


def p_built_in_call_2(p):
    """
     built_in_call : RAND NIL
                    | NOW NIL
                    | UUID NIL
                    | STRUUID NIL
                    | BNODE NIL
    """
    p[0] = Expression(p[1], exp_type = 'builtInNil')


def p_built_in_call_3(p):
    """
     built_in_call : BOUND LPAR VARIABLE RPAR
    """
    p[0] = Expression(p[1], Argument(p[3], False), 'bound')


def p_built_in_call_4(p):
    """
     built_in_call : CONCAT expression_list
                    | COALESCE expression_list
    """
    p[0] = Expression(p[1], p[2], None)


def p_built_in_call_5(p):
    """
    built_in_call : REGEX LPAR expression COMA expression COMA expression RPAR
                      | IF LPAR expression COMA expression COMA expression RPAR
                      | SUBSTR LPAR expression COMA expression COMA expression RPAR
                      | REPLACE LPAR expression COMA expression COMA expression RPAR
    """
    p[0] = Expression(p[1], p[3], [p[5], p[7]])


def p_built_in_call_6(p):
    """
    built_in_call : REPLACE LPAR expression COMA expression COMA expression COMA expression RPAR
    """
    p[0] = Expression(p[1], p[3], [p[5], p[7], p[9]])


def p_built_in_call_7(p):
    """
    built_in_call : EXIST group_graph_pattern
    """
    p[0] = Expression(p[1], p[2])


def p_built_in_call_8(p):
    """
    built_in_call : NOT EXIST group_graph_pattern
    """
    op = p[1] + p[2]
    p[0] = Expression(op, p[3])


def p_built_in_call_9(p):
    """
    built_in_call : aggregate
    """
    p[0] = p[1]


#################################################################


def p_aggregate_0(p):
    """
    aggregate : COUNT LPAR distinct ALL RPAR
    """
    p[0] = Aggregate(Argument(p[4], True), p[3], p[1])


def p_aggregate_1(p):
    """
    aggregate : COUNT LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_2(p):
    """
    aggregate : SUM LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_3(p):
    """
    aggregate : AVG LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_4(p):
    """
    aggregate : MIN LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_5(p):
    """
    aggregate : MAX LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_6(p):
    """
    aggregate : SAMPLE LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_7(p):
    """
    aggregate : GROUP_CONCAT LPAR distinct expression RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1])


def p_aggregate_8(p):
    """
    aggregate : GROUP_CONCAT LPAR distinct expression SEMICOLON SEPARATOR EQUALS CONSTANT RPAR
    """
    p[0] = Aggregate(p[4], p[3], p[1], sep=p[8])


##################################################################


def p_triple_0(p):
    """
    triple : subject predicate object
    """
    p[0] = Triple(p[1], p[2], p[3])


def p_predicate_rdftype(p):
    """
    predicate : ID
    """
    if p[1] == 'a':
        value = '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
        p[0] = Argument(value,True)
    else:
        print('raising')
        p_error(p[1])
        raise SyntaxError


def p_predicate_uri(p):
    """
    predicate : uri
    """
    p[0] = Argument(p[1], True)


def p_predicate_var(p):
    """
    predicate : VARIABLE
    """
    p[0] = Argument(p[1], False)


def p_subject_uri(p):
    """
    subject : uri
    """
    p[0] = Argument(p[1], True)


def p_subject_variable(p):
    """
    subject : VARIABLE
    """
    p[0] = Argument(p[1], False)


def p_object_uri(p):
    """
    object : uri
    """
    p[0] = Argument(p[1], True)


def p_object_variable(p):
    """
    object : VARIABLE
    """
    p[0] = Argument(p[1], False)


def p_object_constant(p):
    """
    object : CONSTANT
    """
    c = p[1].strip()
    p[0] = Argument(p[1], True)
    if xsd in p[1]:
        p[0] = Argument(c[:c.find("^")], True, datatype=c[c.rfind("^")+1:])
    if "@" in p[1]:
        p[0] = Argument(c[:c.find("^")], True, datatype="<" + xsd + "string>", lang=c[c.rfind("@")+1:])


def p_error(p):
    # print(type(p))
    if isinstance(p, str):
        value = p
    else:
        value = p.value
    raise TypeError("unknown text at %r" % (value,))


parser = yacc.yacc(debug=0)


# Helpers
def parse(string):
    return parser.parse(urllib.parse.unquote(string), lexer=lexer)
