from overpassforge.statements import Nodes, Ways, Relations, Areas, Difference, Union
from overpassforge._variables import VariableManager
import pytest

@pytest.fixture
def no_sets():
    return VariableManager()

def test_node_statement(no_sets):
    assert Nodes()._compile(no_sets) == "node;"
    assert Nodes(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_sets) == \
        "node(id:42,43)(50.6,7.0,50.8,7.3);"

def test_way_statement(no_sets):
    assert Ways()._compile(no_sets) == "way;"
    assert Ways(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_sets) == \
        "way(id:42,43)(50.6,7.0,50.8,7.3);"

def test_relation_statement(no_sets):
    assert Relations()._compile(no_sets) == "rel;"
    assert Relations(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_sets) == \
        "rel(id:42,43)(50.6,7.0,50.8,7.3);"

def test_area_statement(no_sets):
    assert Areas()._compile(no_sets) == "area;"
    assert Areas(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_sets) == \
        "area(id:42,43)(50.6,7.0,50.8,7.3);"

def test_difference_statement(no_sets):
    assert Difference(Nodes(ids=(42,43)), Nodes(ids=43))._compile(no_sets) == \
        "(node(id:42,43); - node(43););"

def test_union_statement(no_sets):
    assert Union(Nodes(ids=(42,43)), Nodes(ids=44))._compile(no_sets) == \
        "(node(id:42,43); node(44););"
