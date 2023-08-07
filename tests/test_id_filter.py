from overpassforge.filters import Ids

def test_no_ids(no_vars):
    assert Ids().compile(no_vars) == ""

def test_one_id(no_vars):
    assert Ids(42).compile(no_vars) == "(42)"

def test_many_ids(no_vars):
    assert Ids(10, 11, 12, 13).compile(no_vars) == "(id:10,11,12,13)"