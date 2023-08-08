from overpassforge.statements import Nodes, Union, Difference
from overpassforge._visitors import CycleDetector, DependencyRetriever, traverse_statement
from overpassforge.errors import CircularDependencyError
import pytest

def test_no_cycles():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    traverse_statement(d, CycleDetector())

def test_has_cycle():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    c.statements.append(d)

    with pytest.raises(CircularDependencyError):
        traverse_statement(d, CycleDetector())

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

    u2.statements.append(u3)
    u4.statements.append(u1)
    u4.statements.append(u2)
    u4.statements.append(u3)

    traverse_statement(u4, CycleDetector())

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

    u3.statements.append(u2)
    u1.statements.append(u3)
    u4.statements.append(u2)
    u4.statements.append(u3)

    with pytest.raises(CircularDependencyError):
        traverse_statement(u4, CycleDetector())

def test_reference_count():
    a = Nodes()
    b = Nodes()
    c = Union(a, b)
    d = Union(a, b, c)
    counter = DependencyRetriever()
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

    u2.statements.append(u3)
    u4.statements.append(u1)

    counter = DependencyRetriever()
    traverse_statement(u5, counter)

    assert counter.deps[a].ref_count == 2
    assert counter.deps[d].ref_count == 1
    assert counter.deps[g].ref_count == 2
    assert counter.deps[u2].ref_count == 2
    assert counter.deps[u4].ref_count == 1
    assert counter.deps[u5].ref_count == 1