from overpassforge.statements import RawStatement, Elements, Nodes, Ways, Relations, Areas, Difference, Union
from overpassforge._variables import VariableManager
from overpassforge.filters import *
from overpassforge.errors import UnexpectedCompilationError
import pytest

def test_elements_statement(no_vars):
    assert Elements()._compile(no_vars) == "nwr;"

def test_node_statement(no_vars):
    assert Nodes()._compile(no_vars) == "node;"
    assert Nodes(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_vars) == \
        "node(id:42,43)(50.6,7.0,50.8,7.3);"

def test_way_statement(no_vars):
    assert Ways()._compile(no_vars) == "way;"
    assert Ways(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_vars) == \
        "way(id:42,43)(50.6,7.0,50.8,7.3);"

def test_relation_statement(no_vars):
    assert Relations()._compile(no_vars) == "rel;"
    assert Relations(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_vars) == \
        "rel(id:42,43)(50.6,7.0,50.8,7.3);"

def test_area_statement(no_vars):
    assert Areas()._compile(no_vars) == "area;"
    assert Areas(ids=(42,43), bounding_box=(50.6,7.0,50.8,7.3))._compile(no_vars) == \
        "area(id:42,43)(50.6,7.0,50.8,7.3);"

def test_difference_statement(no_vars):
    assert Difference(Nodes(ids=(42,43)), Nodes(ids=43))._compile(no_vars) == \
        "(node(id:42,43); - node(43););"
    assert (Nodes(ids=(42,43)) - Nodes(ids=43))._compile(no_vars) == \
        "(node(id:42,43); - node(43););"

def test_difference_statement_variable():
    vars = VariableManager()
    u = Difference(Nodes(name="Foo"), Ways(name="Foo"))
    name_u = vars.add_statement(u)
    assert u._compile(vars) == \
        f"""(node["name"="Foo"]; - way["name"="Foo"];)->.{name_u};"""

def test_union_statement(no_vars):
    assert Union(Nodes(ids=(42,43)), Nodes(ids=44))._compile(no_vars) == \
        "(node(id:42,43); node(44););"
    assert (Nodes(ids=(42,43)) + Nodes(ids=44))._compile(no_vars) == \
        "(node(id:42,43); node(44););"

def test_union_statement_variable():
    vars = VariableManager()
    u = Union(Nodes(name="Foo"), Ways(name="Foo"))
    name_u = vars.add_statement(u)
    assert u._compile(vars) == \
        f"""(node["name"="Foo"]; way["name"="Foo"];)->.{name_u};"""

def test_invalid_raw_statement_placeholder():
    with pytest.raises(ValueError):
        RawStatement("node[name=Foo]->.{};")

def test_raw_statement_no_vars(no_vars):
    a = Nodes()
    with pytest.raises(UnexpectedCompilationError):
        RawStatement("node.{missing_var};", missing_var=a)._compile(no_vars)
    
    vars = VariableManager()
    stmt = RawStatement("node[foo];")
    vars.add_statement(stmt)
    with pytest.raises(UnexpectedCompilationError):
        print(stmt._compile(vars))


@pytest.fixture
def vars_with_nodes():
    vars = VariableManager()
    nodes = Nodes()
    nodes_var = vars.add_statement(nodes)
    return vars, nodes, nodes_var

def test_filter_within(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes

    assert nodes.within((10.0,20.0,30.0,40.0))._compile(vars) == \
        f"""node.{nodes_var}(10.0,20.0,30.0,40.0);"""
    
    assert nodes.within(Polygon([42.0], [43.0]))._compile(vars) == \
        f"""node.{nodes_var}(poly:"42.0 43.0");"""
    
    paris = Areas(name="Paris")
    paris_var = vars.add_statement(paris)
    assert nodes.within(paris)._compile(vars) == \
        f"""node.{nodes_var}(area.{paris_var});"""

def test_filter_changed_since(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes

    assert nodes.changed_since(datetime(2023, 1, 1, 7))._compile(vars) == \
        f"""node.{nodes_var}(newer:"2023-01-01T07:00:00Z");"""

def test_filter_changed_between(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes

    assert nodes.changed_between(datetime(2023, 1, 1, 7), datetime(2023, 1, 1, 8))._compile(vars) == \
        f"""node.{nodes_var}(changed:"2023-01-01T07:00:00Z","2023-01-01T08:00:00Z");"""

def test_filter_last_changed_by(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes

    assert nodes.last_changed_by("Steve", 42)._compile(vars) == \
        f"""node.{nodes_var}(uid:42)(user:"Steve");"""

def test_filter_outlines_of(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes

    london = Areas(name="London")
    london_var = vars.add_statement(london)
    assert nodes.outlines_of(london)._compile(vars) == \
        f"""node.{nodes_var}(pivot.{london_var});"""

def test_filter_around(vars_with_nodes: tuple[VariableManager, Nodes, str]):
    vars, nodes, nodes_var = vars_with_nodes
    
    nodes_around = Nodes(name="Foo")
    around_var = vars.add_statement(nodes_around)
    assert nodes.around(100.0, nodes_around)._compile(vars) == \
        f"""node.{nodes_var}(around.{around_var}:100.0);"""