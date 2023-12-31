from overpassforge.filters import Intersect
from overpassforge.statements import Statement
from overpassforge._variables import VariableManager
from overpassforge.errors import InvalidFilterAttributes
import pytest

def test_one_intersections():
    a = Statement()
    vars = VariableManager()
    name_a = vars.add_statement(a)
    assert Intersect(a)._compile(vars) == f".{name_a}"

def test_two_intersections():
    a = Statement()
    b = Statement()
    vars = VariableManager()
    name_a = vars.add_statement(a)
    name_b = vars.add_statement(b)
    assert Intersect(a, b)._compile(vars) == f".{name_a}.{name_b}"

def test_requires_variable():
    a = Statement()
    b = Statement()
    vars = VariableManager()
    vars.add_statement(a)

    with pytest.raises(KeyError):
        Intersect(a, b)._compile(vars)

def test_empty_intersection(no_vars):
    with pytest.raises(InvalidFilterAttributes):
        Intersect()._compile(no_vars)