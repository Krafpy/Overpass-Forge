import pytest
from overpass_builder.filters import Around
from overpass_builder.base import Statement
from overpass_builder.variables import VariableManager

def test_too_many_attributes():
    a = Statement()
    vars = VariableManager()
    with pytest.raises(AttributeError):
        Around(100.0, a, [10.0], [10.0]).compile(vars)

def test_no_attributes():
    with pytest.raises(AttributeError):
        Around(100.0).compile(VariableManager())

def test_around_set():
    a = Statement()
    vars = VariableManager()
    name = vars.add_statement(a)
    assert Around(10.0, a).compile(vars) == f"(around.{name}:10.0)"

def test_around_one_point():
    around = Around(10.0, lats=[42.0], lons=[43.0])
    assert around.compile(VariableManager()) == f"(around:10.0,42.0,43.0)"

def test_around_many_points():
    around = Around(10.0, lats=[42.0, -21.0], lons=[43.0, 17.5, 31.0])
    assert around.compile(VariableManager()) == f"(around:10.0,42.0,43.0,-21.0,17.5)"