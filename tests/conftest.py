import pytest
from overpassforge.variables import VariableManager

@pytest.fixture
def no_vars():
    return VariableManager()