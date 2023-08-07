from overpassforge.filters import Tag, K, V

def test_equal(no_vars):
    assert (K("amenity") == V("cinema"))._compile(no_vars) == """["amenity"="cinema"]"""
    assert (K("tourism") == "yes")._compile(no_vars) == """["tourism"="yes"]"""

def test_not_equal(no_vars):
    assert (K("amenity") != V("cinema"))._compile(no_vars) == """["amenity"!="cinema"]"""
    assert (K("tourism") != "yes")._compile(no_vars) == """["tourism"!="yes"]"""

def test_has_key(no_vars):
    assert Tag.has("opening_hours")._compile(no_vars) == """["opening_hours"]"""

def test_has_not_key(no_vars):
    assert Tag.hasnot("opening_hours")._compile(no_vars) == """[!"opening_hours"]"""

def test_value_matches(no_vars):
    assert (K("name") == V("^Foo$", True))._compile(no_vars) == """["name"~"^Foo$"]"""

def test_value_not_matches(no_vars):
    assert (K("name") != V("^Foo$", True))._compile(no_vars) == """["name"!~"^Foo$"]"""

def test_key_value_match(no_vars):
    assert (K("^addr:.*$", True) == V("^Foo$", True))._compile(no_vars) == """[~"^addr:.*$"~"^Foo$"]"""

def test_case_insensitive(no_vars):
    tag = K("amenity") == V("cinema")
    tag.case_sensitive = False
    assert tag._compile(no_vars) == """["amenity"="cinema",i]"""