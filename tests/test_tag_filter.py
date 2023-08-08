from overpassforge.filters import Key, Regex

def test_equal(no_vars):
    assert (Key("amenity") == "cinema")._compile(no_vars) == """["amenity"="cinema"]"""

def test_not_equal(no_vars):
    assert (Key("amenity") != "cinema")._compile(no_vars) == """["amenity"!="cinema"]"""

def test_has_key(no_vars):
    assert Key("opening_hours")._compile(no_vars) == """["opening_hours"]"""

def test_has_not_key(no_vars):
    assert (~Key("opening_hours"))._compile(no_vars) == """[!"opening_hours"]"""

def test_value_matches(no_vars):
    assert (Key("name") == Regex("^Foo$"))._compile(no_vars) == """["name"~"^Foo$"]"""

def test_value_not_matches(no_vars):
    assert (Key("name") != Regex("^Foo$"))._compile(no_vars) == """["name"!~"^Foo$"]"""

def test_key_value_match(no_vars):
    assert (Key(Regex("^addr:.*$")) == Regex("^Foo$"))._compile(no_vars) == """[~"^addr:.*$"~"^Foo$"]"""

def test_case_insensitive(no_vars):
    tag = Key("amenity") == "cinema"
    tag.case_sensitive = False
    assert tag._compile(no_vars) == """["amenity"="cinema",i]"""