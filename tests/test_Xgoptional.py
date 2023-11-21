from multiprocessing import Queue

from DeTrusty.Operators.AnapsidOperators.Xgoptional import Xgoptional
from tests.utils import is_equal


def test_xgoptional_single_variable():
    out = Queue()
    var_left = ['a', 'b']
    var_right = ['a', 'c']
    op = Xgoptional(var_left, var_right)
    que1 = Queue()
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'b_A1'}
    })
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A2'},
        'b': {'type': 'literal', 'value': 'b_A2'}
    })  # no match in right
    que1.put('EOF')
    que2 = Queue()
    que2.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'c': {'type': 'literal', 'value': 'c_A1'}
    })
    que2.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A3'},
        'c': {'type': 'literal', 'value': 'c_A3'}
    })  # no match in left
    que2.put('EOF')
    que3 = Queue()
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'b_A1'},
        'c': {'type': 'literal', 'value': 'c_A1'}
    })
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A2'},
        'b': {'type': 'literal', 'value': 'b_A2'},
        'c': {'value': ''}
    })
    que3.put('EOF')
    op.execute(que1, que2, out)
    assert is_equal(out, que3) is True


def test_xgoptional_two_variables():
    out = Queue()
    var_left = ['a', 'b', 'c']
    var_right = ['a', 'b', 'd']
    op = Xgoptional(var_left, var_right)
    que1 = Queue()
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'B1'},
        'c': {'type': 'typed-literal', 'value': '1', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'}
    })
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A2'},
        'b': {'type': 'literal', 'value': 'B2'},
        'c': {'type': 'typed-literal', 'value': '2', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'}
    })  # no match in right
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A4'},
        'b': {'type': 'literal', 'value': 'B4'},
        'c': {'type': 'typed-literal', 'value': '4', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'}
    })  # partial match in right
    que1.put('EOF')
    que2 = Queue()
    que2.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'B1'},
        'd': {'type': 'literal', 'value': 'd1'}
    })
    que2.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A3'},
        'b': {'type': 'literal', 'value': 'B3'},
        'd': {'type': 'literal', 'value': 'd3'}
    })  # no match in left
    que2.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A4'},
        'b': {'type': 'literal', 'value': 'B41'},
        'd': {'type': 'literal', 'value': 'd4'}
    })  # partial match in left
    que2.put('EOF')
    que3 = Queue()
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'B1'},
        'c': {'type': 'typed-literal', 'value': '1', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'},
        'd': {'type': 'literal', 'value': 'd1'}
    })
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A2'},
        'b': {'type': 'literal', 'value': 'B2'},
        'c': {'type': 'typed-literal', 'value': '2', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'},
        'd': {'value': ''}
    })
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A4'},
        'b': {'type': 'literal', 'value': 'B4'},
        'c': {'type': 'typed-literal', 'value': '4', 'datatype': 'http://www.w3.org/2001/XMLSchema#integer'},
        'd': {'value': ''}
    })
    que3.put('EOF')
    op.execute(que1, que2, out)
    assert is_equal(out, que3) is True


def test_xgoptional_non_matching_type():
    out = Queue()
    var_left = ['a', 'b']
    var_right = ['a', 'c']
    op = Xgoptional(var_left, var_right)
    que1 = Queue()
    que1.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'b_A1'}
    })
    que1.put('EOF')
    que2 = Queue()
    que2.put({
        'a': {'type': 'literal', 'value': 'https://example.com/A1'},
        'c': {'type': 'literal', 'value': 'c_A1'}
    })
    que2.put('EOF')
    que3 = Queue()
    que3.put({
        'a': {'type': 'uri', 'value': 'https://example.com/A1'},
        'b': {'type': 'literal', 'value': 'b_A1'},
        'c': {'type': 'literal', 'value': 'c_A1'}
    })
    que3.put('EOF')
    op.execute(que1, que2, out)
    assert is_equal(out, que3) is True
