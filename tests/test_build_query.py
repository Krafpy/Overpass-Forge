from overpassforge.builder import build, Settings
from overpassforge.statements import RawStatement, Nodes, Difference, Union, Areas, Ways
from overpassforge.filters import *
import pytest

def test_no_dependencies_1():
    assert build(Nodes().where(amenity="restaurant")) == \
        """node["amenity"="restaurant"];"""

def test_no_dependencies_2():
    a = Nodes(ids=128)
    b = Nodes(bounding_box=(42.0, 43.0, 44.0, 45.0))
    u1 = Union(a, b)
    assert build(u1) == """(node(128); node(42.0,43.0,44.0,45.0););"""

def test_with_settings():
    a = Nodes(ids=128)
    b = Nodes(bounding_box=(42.0, 43.0, 44.0, 45.0))
    u1 = Union(a, b)
    assert build(u1, Settings()) == \
        """[out:json][timeout:25];\n""" \
        """(node(128); node(42.0,43.0,44.0,45.0););"""

def test_complex_tag_filtering():
    a = Nodes().where(Regex("^addr:.*$"), name=Regex("^Foo.*$"))
    tag = Key("opening_hours") != Regex(".*mo.*")
    tag.case_sensitive = False
    a = a.filter(tag)
    assert build(a) == \
        """node[~"^addr:.*$"]["name"~"^Foo.*$"]["opening_hours"!~".*mo.*",i];"""

def test_one_dependency():
    a = Nodes(ids=128)
    b = Nodes(bounding_box=(42.0, 43.0, 44.0, 45.0))
    c = Nodes(ids=(16, 32))
    u1 = Union(a, b)
    u2 = Union(b, c)
    d1 = Difference(u1, u2)
    assert build(d1) == \
    """node(42.0,43.0,44.0,45.0)->.set_0;\n""" \
    """((node(128); .set_0;); - (.set_0; node(id:16,32);););"""

def test_with_one_out():
    a = Nodes(ids=42).out(" body geom", " meta  ", (10.0,20.0,30.0,40.0))
    assert build(a) == \
        "node(42);\n" \
        "out (10.0, 20.0, 30.0, 40.0) body geom meta;"

def test_with_two_out():
    a = Nodes(ids=42)
    a.out("body")
    b = Nodes(ids=43)
    u = Union(a, b)
    u.out("geom")
    assert build(u) == \
        "node(42)->.set_0;\n" \
        ".set_0 out body;\n" \
        "(.set_0; node(43););\n" \
        "out geom;"

def test_filter_dependency():
    a = Nodes(bounding_box=(10.0, 20.0, 30.0, 40.0))
    b = Nodes(input_set=a).where(amenity="bar")
    b.out()
    u = a + b
    u.out()
    assert build(u) == \
        "node(10.0,20.0,30.0,40.0)->.set_0;\n" \
        "node.set_0[\"amenity\"=\"bar\"]->.set_1;\n" \
        ".set_1 out;\n" \
        "(.set_0; .set_1;);\n" \
        "out;"

def test_chained_filters():
    a = Nodes()
    b = a.where(amenity="bar")
    c = b.where(parking="yes")
    d = c.where(tourism="yes")
    assert build(d) == """node["amenity"="bar"]["parking"="yes"]["tourism"="yes"];"""

def test_simple_raw_statement():
    assert build(RawStatement("something")) == "something"

def test_raw_statement():
    a = Nodes().where(amenity="bar")
    b = Nodes(input_set=a).where(tourism="yes")
    c = RawStatement("(.{y}; - .{x};) -> .items;", x=a, y=b)
    assert build(c) == \
        """node["amenity"="bar"]->.set_0;\n""" \
        """node.set_0["tourism"="yes"]->.set_1;\n""" \
        """(.set_1; - .set_0;) -> .items;"""

def test_dependent_raw_statements():
    a = RawStatement("node[\"tourism\"=\"hotel\"] -> .{:out_var};")
    b = RawStatement("node[\"amenity\"=\"bar\"] -> .{:out_var};")
    c = RawStatement("(.{x}; - .{y};);", x=a, y=b)
    assert build(c) == \
        "node[\"tourism\"=\"hotel\"] -> .set_0;\n" \
        "node[\"amenity\"=\"bar\"] -> .set_1;\n" \
        "(.set_0; - .set_1;);"

def test_area_filter():
    bus_stops = Nodes(within=Areas(name="Bonn"), highway="bus_stop")
    ways = Ways(around=(bus_stops, 100.0)).where(amenity="cinema")
    nodes = Nodes(around=Around(100.0, bus_stops)).where(amenity="cinema")
    assert build((ways + nodes).out("meta")) == \
        """area["name"="Bonn"]->.set_0;\n""" \
        """node(area.set_0)["highway"="bus_stop"]->.set_1;\n""" \
        """(way(around.set_1:100.0)["amenity"="cinema"]; node(around.set_1:100.0)["amenity"="cinema"];);\n""" \
        """out meta;"""

def test_chained_outs():
    a = Nodes(amenity="cinema")
    a.out("body")
    a.out(" geom    skel")
    assert build(a) == \
        "node[\"amenity\"=\"cinema\"];\n" \
        "out body;\n" \
        "out geom skel;"

def test_invalid_out_options():
    with pytest.raises(ValueError):
        Nodes().out("not an option")


def test_consecutive_builds():
    # This test fail if the compilation modifies the statements in-place
    a = Nodes(name="Foo")
    b = Nodes(input_set=a, name="Bar")
    u = a + b
    assert build(b) == """node["name"="Foo"]["name"="Bar"];"""
    assert build(u) == \
        """node["name"="Foo"]->.set_0;\n""" \
        """(.set_0; node.set_0["name"="Bar"];);"""

def test_labelled_statements():
    a = Areas(name="Foo", label="a")
    u = Union(Nodes(within=a), Ways(within=a), label="union")
    u.out()
    d = Difference(a, u, "result") # Label will be ignored as it is the last statement
    d.out()
    assert build(d) == \
        """area["name"="Foo"]->.a;\n""" \
        """(node(area.a); way(area.a);)->.union;\n""" \
        """.union out;\n""" \
        """(.a; - .union;);\n""" \
        """out;"""

def test_labelled_raw_statement():
    a = RawStatement("node[name=\"Foo\"]->.{:out_var};", label="raw_statement")
    b = Nodes(amenity="cinema").intersection(a)
    b.out()
    assert build(b) == \
        """node[name="Foo"]->.raw_statement;\n""" \
        """node["amenity"="cinema"].raw_statement;\n""" \
        """out;"""

def test_different_query_simplficiation():
    n = Nodes(name="Foo")
    w = Ways(name="Bar", input_set=n)
    assert build(w) == \
        """node["name"="Foo"]->.set_0;\n""" \
        """way.set_0["name"="Bar"];"""

def test_filter_on_union():
    u = Nodes(42) + Ways(42)
    u = u.where(name="Foo")
    assert build(u) == \
        """(node(42); way(42);)->.set_0;\n""" \
        """nwr.set_0["name"="Foo"];"""

def test_filter_on_difference():
    d = Nodes(42) - Ways(42)
    d = d.where(name="Foo")
    assert build(d) == \
        """(node(42); - way(42);)->.set_0;\n""" \
        """nwr.set_0["name"="Foo"];"""