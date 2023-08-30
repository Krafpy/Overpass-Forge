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
    r = RecurseDown(a, label="b")
    assert r._compile(no_vars) == ">;"
    assert r._compile(vars) == ".a >;"

    vars = VariableManager()
    vars.add_statement(r)
    assert r._compile(vars) == "> ->.b;"
    vars.add_statement(a)
    assert r._compile(vars) == ".a > ->.b;"

    assert a.recursed_down()._compile(no_vars) == ">;"

def test_recurse_down_rels(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    r = RecurseDownRels(a, label="b")
    assert r._compile(no_vars) == ">>;"
    assert r._compile(vars) == ".a >>;"

    vars = VariableManager()
    vars.add_statement(r)
    assert r._compile(vars) == ">> ->.b;"
    vars.add_statement(a)
    assert r._compile(vars) == ".a >> ->.b;"

    assert a.recursed_down_rels()._compile(no_vars) == ">>;"

def test_recurse_up(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    r = RecurseUp(a, label="b")
    assert r._compile(no_vars) == "<;"
    assert r._compile(vars) == ".a <;"
    
    vars = VariableManager()
    vars.add_statement(r)
    assert r._compile(vars) == "< ->.b;"
    vars.add_statement(a)
    assert r._compile(vars) == ".a < ->.b;"

    assert a.recursed_up()._compile(no_vars) == "<;"

def test_recurse_up_rels(vars_with_node: tuple[Nodes, VariableManager], no_vars):
    a, vars = vars_with_node
    r = RecurseUpRels(a, label="b")
    assert r._compile(no_vars) == "<<;"
    assert r._compile(vars) == ".a <<;"

    vars = VariableManager()
    vars.add_statement(r)
    assert r._compile(vars) == "<< ->.b;"
    vars.add_statement(a)
    assert r._compile(vars) == ".a << ->.b;"    

    assert a.recursed_up_rels()._compile(no_vars) == "<<;"