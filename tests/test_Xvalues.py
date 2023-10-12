import pytest

from DeTrusty.Operators.AnapsidOperators.Xvalues import Xvalues
from DeTrusty.Sparql.Parser.services import Argument, Values


@pytest.fixture
def value_one():
    vars1 = Values([Argument('?disease_name')], [[Argument("\"Attention-deficit_hyperactivity_disorder\"", True)]])
    return Xvalues(vars1)

@pytest.fixture
def value_two():
    vars2 = Values([Argument('?disease_name')], [[None, True]])
    return Xvalues(vars2)

def test_xvalues_filter_by_value_valid(value_one):
    tuple_ = {'disease_name': 'Attention-deficit_hyperactivity_disorder'}
    assert value_one.filterByValues(tuple_) == True

def test_xvalues_filter_by_value_undef(value_two):
    tuple_ = {'disease_name': 'Rheumatoid_arthritis'}
    assert value_two.filterByValues(tuple_) == True

def test_xvalues_filter_by_value_invalid(value_one):
    tuple_ = {'disease_name': 'Rheumatoid_arthritis'}
    assert value_one.filterByValues(tuple_) == False

def test_xvalues_filter_by_value_multi_var_input_valid(value_one):
    tuple_ = {'disease_name': 'Attention-deficit_hyperactivity_disorder', 'drug_gn': 'Methylphenidate'}
    assert value_one.filterByValues(tuple_) == True

def test_xvalues_filter_by_value_multi_var_input_invalid(value_one):
    tuple_ = {'disease_name': 'Response to morphine-6-glucuronide', 'drug_gn': 'Heroin'}
    assert value_one.filterByValues(tuple_) == False
