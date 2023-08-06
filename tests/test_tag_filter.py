from overpass_builder.filters import (
    KeyExists,
    KeyNotExists,
    KeyNotEqualsValue,
    KeyEqualsValue,
    KeyValueMatchExprs,
    ValueMatchesExpr,
    ValueNotMatchesExpr,
    InvalidRegexError
)
import pytest

def test_equal(no_vars):
    assert KeyEqualsValue("amenity", "restaurant").compile(no_vars) == "[\"amenity\"=\"restaurant\"]"

def test_not_equal(no_vars):
    assert KeyNotEqualsValue("amenity", "bar").compile(no_vars) == "[\"amenity\"!=\"bar\"]"

def test_exists(no_vars):
    assert KeyExists("opening_hours").compile(no_vars) == "[\"opening_hours\"]"

def test_not_exists(no_vars):
    assert KeyNotExists("opening_hours").compile(no_vars) == "[!\"opening_hours\"]"

def test_value_matches(no_vars):
    assert ValueMatchesExpr("name", "^Foo$").compile(no_vars) == "[\"name\"~\"^Foo$\"]"
    
    with pytest.raises(InvalidRegexError):
        ValueMatchesExpr("name", "*Foo").compile(no_vars)

def test_value_not_matches(no_vars):
    assert ValueNotMatchesExpr("name", "^Foo$").compile(no_vars) == "[\"name\"!~\"^Foo$\"]"
    
    with pytest.raises(InvalidRegexError):
        ValueNotMatchesExpr("name", "*Foo").compile(no_vars)

def test_key_value_match(no_vars):
    assert KeyValueMatchExprs("^addr:.*$", "^Foo$").compile(no_vars) == "[~\"^addr:.*$\"~\"^Foo$\"]"

    with pytest.raises(InvalidRegexError):
        assert KeyValueMatchExprs("*addr:.*$", "^Foo$").compile(no_vars)
    with pytest.raises(InvalidRegexError):
        assert KeyValueMatchExprs("^addr:.*$", "*Foo$").compile(no_vars)