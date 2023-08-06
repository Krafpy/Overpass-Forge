import pytest
from overpass_builder.variables import VariableManager

@pytest.fixture
def no_vars():
    return VariableManager()