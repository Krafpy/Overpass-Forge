from overpassforge.filters import Filter, BoundingBox, Newer, Changed, User, Area, Pivot, Polygon
from overpassforge.statements import Areas
from overpassforge._variables import VariableManager
from datetime import datetime

def test_raw_filter(no_vars):
    assert Filter("some filter")._compile(no_vars) == "some filter"

def test_bounding_box(no_vars):
    assert BoundingBox(50.6,7.0,50.8,7.3)._compile(no_vars) == "(50.6,7.0,50.8,7.3)"

def test_newer(no_vars):
    assert Newer(datetime(2012, 9, 14, 7))._compile(no_vars) == "(newer:\"2012-09-14T07:00:00Z\")"

def test_changed_one(no_vars):
    assert Changed(datetime(2012, 9, 14, 7))._compile(no_vars) == "(changed:\"2012-09-14T07:00:00Z\")"

def test_changed_two(no_vars):
    c = Changed(datetime(2012, 9, 14, 7), datetime(2012, 9, 14, 7, 1))
    assert c._compile(no_vars) == "(changed:\"2012-09-14T07:00:00Z\",\"2012-09-14T07:01:00Z\")"

def test_user_name(no_vars):
    assert User("Steve")._compile(no_vars) == "(user:\"Steve\")"

def test_user_id(no_vars):
    assert User(1)._compile(no_vars) == "(uid:1)"

def test_user_ids_names(no_vars):
    assert User("Steve",1,2,"Paul",3)._compile(no_vars) == "(uid:1,2,3)(user:\"Steve\",\"Paul\")"

def test_area_filter():
    a = Areas()
    vars = VariableManager()
    name = vars.add_statement(a)
    assert Area(a)._compile(vars) == f"(area.{name})"

def test_pivot_filter():
    a = Areas()
    vars = VariableManager()
    name = vars.add_statement(a)
    assert Pivot(a)._compile(vars) == f"(pivot.{name})"

def test_polygon_filter(no_vars):
    p = Polygon([50.7,50.7,50.75], [7.1,7.2,7.15])
    assert p._compile(no_vars) == "(poly:\"50.7 7.1 50.7 7.2 50.75 7.15\")"