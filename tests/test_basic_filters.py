from overpass_builder.filters import BoundingBox

def test_bounding_box(no_vars):
    assert BoundingBox(50.6,7.0,50.8,7.3).compile(no_vars) == "(50.6,7.0,50.8,7.3)"