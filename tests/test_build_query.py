from overpass_builder.builder import build
from overpass_builder.statements import Nodes, Difference, Union, Statement

def test_no_dependencies_1():
    assert build(Nodes().where(amenity="restaurant")) == \
        """node["amenity"="restaurant"];"""

def test_no_dependencies_2():
    a = Nodes(ids=128)
    b = Nodes(bounding_box=(42.0, 43.0, 44.0, 45.0))
    u1 = Union(a, b)
    assert build(u1) == """(node(128); node(42.0,43.0,44.0,45.0););"""

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
    a = Nodes(ids=42).out("body")
    b = Nodes(ids=43)
    u = Union(a, b).out("geom")
    assert build(u) == \
        "node(42)->.set_0;\n" \
        ".set_0 out body;\n" \
        "(.set_0; node(43););\n" \
        "out geom;"

def test_filter_dependency():
    a = Nodes(bounding_box=(10.0, 20.0, 30.0, 40.0))
    b = Nodes(input_set=a).where(amenity="bar").out()
    u = (a + b).out()
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

def test_raw_statement():
    a = Nodes().where(amenity="bar")
    b = Nodes(input_set=a).where(tourism="yes")
    c = Statement("(.{y}; - .{x};) -> .items;", x=a, y=b)
    assert build(c) == \
        """node["amenity"="bar"]->.set_0;\n""" \
        """node.set_0["tourism"="yes"]->.set_1;\n""" \
        """(.set_1; - .set_0;) -> .items;"""