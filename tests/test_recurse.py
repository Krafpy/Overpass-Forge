from overpassforge.statements import RecurseDown, RecurseDownRels, RecurseUp, RecurseUpRels, Nodes
from overpassforge._variables import VariableManager
import pytest

@pytest.fixture
def vars_with_node():
    a = Nodes(name="Foo", label="a")
    vars = VariableManager()
    vars.add_statement(a)
    return a, vars

def test_recurse_down(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    assert RecurseDown(a)._compile(no_vars) == ">;"
    assert RecurseDown(a)._compile(vars) == ".a >;"
    assert RecurseDown(a)._compile(no_vars, "b") == "> ->.b;"
    assert RecurseDown(a)._compile(vars, "b") == ".a > ->.b;"
    assert a.recursed_down()._compile(no_vars) == ">;"

def test_recurse_down_rels(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    assert RecurseDownRels(a)._compile(no_vars) == ">>;"
    assert RecurseDownRels(a)._compile(vars) == ".a >>;"
    assert RecurseDownRels(a)._compile(no_vars, "b") == ">> ->.b;"
    assert RecurseDownRels(a)._compile(vars, "b") == ".a >> ->.b;"
    assert a.recursed_down_rels()._compile(no_vars) == ">>;"

def test_recurse_up(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    assert RecurseUp(a)._compile(no_vars) == "<;"
    assert RecurseUp(a)._compile(vars) == ".a <;"
    assert RecurseUp(a)._compile(no_vars, "b") == "< ->.b;"
    assert RecurseUp(a)._compile(vars, "b") == ".a < ->.b;"
    assert a.recursed_up()._compile(no_vars) == "<;"

def test_recurse_up_rels(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    assert RecurseUpRels(a)._compile(no_vars) == "<<;"
    assert RecurseUpRels(a)._compile(vars) == ".a <<;"
    assert RecurseUpRels(a)._compile(no_vars, "b") == "<< ->.b;"
    assert RecurseUpRels(a)._compile(vars, "b") == ".a << ->.b;"
    assert a.recursed_up_rels()._compile(no_vars) == "<<;"