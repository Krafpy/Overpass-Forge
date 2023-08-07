import pytest
from overpassforge._variables import VariableManager

@pytest.fixture
def no_vars():
    return VariableManager()