from overpassforge.statements import OverlappingAreas, Nodes
from overpassforge._variables import VariableManager
from overpassforge.errors import InvalidStatementAttributes
import pytest

@pytest.fixture
def vars_with_node():
    a = Nodes(name="Foo", label="a")
    vars = VariableManager()
    vars.add_statement(a)
    return a, vars

def test_covering_area_set(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    assert OverlappingAreas(input_set=a)._compile(no_vars) == "is_in;"
    assert OverlappingAreas(input_set=a)._compile(vars) == ".a is_in;"
    assert OverlappingAreas(input_set=a)._compile(no_vars, "b") == "is_in ->.b;"
    assert OverlappingAreas(input_set=a)._compile(vars, "b") == ".a is_in ->.b;"

def test_covering_area_latlon(no_vars):
    assert OverlappingAreas(lat=42.0, lon=43.0)._compile(no_vars) == "is_in(42.0,43.0);"
    assert OverlappingAreas(lat=42.0, lon=43.0)._compile(no_vars, "b") == "is_in(42.0,43.0) ->.b;"

def test_covering_area_invalid(no_vars):
    with pytest.raises(InvalidStatementAttributes):
        OverlappingAreas()._compile(no_vars)
    
    with pytest.raises(InvalidStatementAttributes):
        OverlappingAreas(None, 43.0, Nodes())._compile(no_vars)
    
    with pytest.raises(InvalidStatementAttributes):
        OverlappingAreas(42.0, 43.0, Nodes())._compile(no_vars)