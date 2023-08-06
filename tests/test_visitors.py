from overpass_builder.statements import Nodes, Union, Difference
from overpass_builder.visitors import CycleDetectionVisitor, CircularDependencyError, DependencyRetrievalVisitor, traverse_statement
import pytest

def test_no_cycles():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    traverse_statement(d, CycleDetectionVisitor())

def test_has_cycle():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    c.elements.append(d)

    with pytest.raises(CircularDependencyError):
        traverse_statement(d, CycleDetectionVisitor())

def test_complex_no_cycle():
    a = Nodes()
    b = Nodes()
    c = Nodes()
    d = Nodes()
    e = Nodes()
    f = Nodes()
    g = Nodes()

    u1 = Union(a, b)
    u2 = Union(c, d, u1)
    u3 = Union(e, f)
    u4 = Union(g, u2, u3)

    u2.elements.append(u3)
    u4.elements.append(u1)
    u4.elements.append(u2)
    u4.elements.append(u3)

    traverse_statement(u4, CycleDetectionVisitor())

def test_complex_has_cycle():
    a = Nodes()
    b = Nodes()
    c = Nodes()
    d = Nodes()
    e = Nodes()
    f = Nodes()
    g = Nodes()

    u1 = Union(a, b)
    u2 = Union(c, d, u1)
    u3 = Union(e, f)
    u4 = Union(g, u2, u3)

    u3.elements.append(u2)
    u1.elements.append(u3)
    u4.elements.append(u2)
    u4.elements.append(u3)

    with pytest.raises(CircularDependencyError):
        traverse_statement(u4, CycleDetectionVisitor())

def test_reference_count():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    counter = DependencyRetrievalVisitor()
    traverse_statement(d, counter)

    assert counter.deps[a].ref_count == 2
    assert counter.deps[b].ref_count == 2
    assert counter.deps[c].ref_count == 1
    assert counter.deps[d].ref_count == 1

def test_complex_reference_count():
    a = Nodes()
    b = Nodes()
    c = Nodes().intersection(a)
    d = Nodes()
    e = Nodes()
    f = Nodes()
    g = Nodes()

    u1 = Union(a, b)
    u2 = Union(c, d, u1)
    u3 = Union(e, f)
    u4 = Union(g, u2, u3)
    u5 = Union(u2, u4, g)

    u2.elements.append(u3)
    u4.elements.append(u1)

    counter = DependencyRetrievalVisitor()
    traverse_statement(u5, counter)

    assert counter.deps[a].ref_count == 2
    assert counter.deps[d].ref_count == 1
    assert counter.deps[g].ref_count == 2
    assert counter.deps[u2].ref_count == 2
    assert counter.deps[u4].ref_count == 1
    assert counter.deps[u5].ref_count == 1