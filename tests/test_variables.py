from overpassforge._variables import VariableManager
from overpassforge.statements import Nodes
from overpassforge.errors import UnexpectedCompilationError
import pytest

def test_is_named():
    a = Nodes()
    b = Nodes()
    vars = VariableManager()
    vars.add_statement(a)
    
    assert vars.is_named(a)
    assert not vars.is_named(b)

def test_add_existing_statement():
    vars = VariableManager()
    a = Nodes()
    vars.add_statement(a)
    with pytest.raises(UnexpectedCompilationError) as exc_info:
        vars.add_statement(a)
    assert exc_info.value.statement == a