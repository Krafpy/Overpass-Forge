from overpass_builder.filters import BoundingBox, Newer, Changed, User, InArea, Pivot
from overpass_builder.statements import Areas
from overpass_builder.variables import VariableManager
from datetime import datetime

def test_bounding_box(no_vars):
    assert BoundingBox(50.6,7.0,50.8,7.3).compile(no_vars) == "(50.6,7.0,50.8,7.3)"

def test_newer(no_vars):
    assert Newer(datetime(2012, 9, 14, 7)).compile(no_vars) == "(newer:\"2012-09-14T07:00:00Z\")"

def test_changed_one(no_vars):
    assert Changed(datetime(2012, 9, 14, 7)).compile(no_vars) == "(changed:\"2012-09-14T07:00:00Z\")"

def test_changed_two(no_vars):
    c = Changed(datetime(2012, 9, 14, 7), datetime(2012, 9, 14, 7, 1))
    assert c.compile(no_vars) == "(changed:\"2012-09-14T07:00:00Z\",\"2012-09-14T07:01:00Z\")"

def test_user_name(no_vars):
    assert User("Steve").compile(no_vars) == "(user:\"Steve\")"

def test_user_id(no_vars):
    assert User(1).compile(no_vars) == "(uid:1)"

def test_user_ids_names(no_vars):
    assert User("Steve",1,2,"Paul",3).compile(no_vars) == "(uid:1,2,3)(user:\"Steve\",\"Paul\")"

def test_area_filter():
    a = Areas()
    vars = VariableManager()
    name = vars.add_statement(a)
    assert InArea(a).compile(vars) == f"(area.{name})"

def test_pivot_filter():
    a = Areas()
    vars = VariableManager()
    name = vars.add_statement(a)
    assert Pivot(a).compile(vars) == f"(pivot.{name})"