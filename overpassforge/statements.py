from __future__ import annotations

from overpassforge.base import Set
from overpassforge.filters import Filter
from .base import Statement, Set
from ._variables import VariableManager as _VariableManager
from .errors import UnexpectedCompilationError
from .filters import (
    Filter,
    BoundingBox,
    Ids,
    Key,
    Intersection,
    Around,
    Area,
)
from typing import Iterable


class RawStatement(Statement):
    """Represents a raw Overpass query string. It can be formated to support dependency
    from other statements (raw or not).

    Example:

    >>> foo = Nodes().where(name="Foo")
    >>> bar = Statement("node.{x}[amenity=\\"bar\\"]->.{:out_var};", x=foo)
    >>> baz = Nodes(input_set=bar).within((50.6,7.0,50.8,7.3))
    >>> print(build(baz))
    node["name"="Foo"]->.set_0;
    node.set_0[amenity="bar"]->.set_1;
    node.set_1(50.6,7.0,50.8,7.3);
    """

    def __init__(self, raw: str = "", label: str | None = None, **dependencies: Statement) -> None:
        """
        Args:
            raw: A formatable string of the query. Named placeholders
                (e.g. "{name}") indicating dependency on other statements. An
                optional special {:out_var} placeholder indicates where the name of
                the output set must be placed.
            dependencies: The list of statements whose results it depends on
                Their keyword names must match the placeholders in the raw query string.
        
        Raises:
            ValueError: Invalid unamed placholder "{}".
        """

        super().__init__(label)

        self._raw = raw
        self._dependency_list = dependencies
        if "{}" in raw:
            raise ValueError("All inserted dependencies must be named.")
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        """Compiles the statement into its Overpass query string, without eventual
        outputs.
        """
        var_names: dict[str, str] = {}
        for name, stmt in self._dependency_list.items():
            if not vars.is_named(stmt):
                raise UnexpectedCompilationError("All inserted sets must use variables.")
            var_names[name] = vars[stmt]
        compiled = self._raw
        if "{:out_var}" in self._raw:
            compiled = compiled.replace("{:out_var}", out_var or "_")
        elif out_var is not None:
            raise UnexpectedCompilationError("No output variable specified.")
        return compiled.format(**var_names)
    
    @property
    def _dependencies(self) -> list[Statement]:
        """List of statements on which this statement depends on."""
        return list(self._dependency_list.values())


class Elements(Set):
    """Represents a query set, e.g. node, rel, way..."""

    _type_specifier: str = "nwr"
    
    def __init__(self,
        ids: Iterable[int] | int | None = None,
        label: str | None = None, *,
        bounding_box: tuple[float, float, float, float] | None = None,
        input_set: Statement | None = None,
        within: Areas | None = None,
        around: tuple[Statement, float] | Around | None = None,
        filters: Iterable[Filter] = [],
        **tags: str
    ) -> None:
        
        super().__init__(filters, label)

        if isinstance(input_set, Statement):
            self.filters.append(Intersection(input_set))

        if isinstance(ids, int):
            self.filters.append(Ids(ids))
        elif ids is not None:
            self.filters.append(Ids(*ids))

        if bounding_box is not None:
            self.filters.append(BoundingBox(*bounding_box))
        
        if within is not None:
            self.filters.append(Area(within))
        
        if isinstance(around, Around):
            self.filters.append(around)
        elif around is not None:
            self.filters.append(Around(around[1], around[0]))
        
        for key, value in tags.items():
            self.filters.append(Key(key) == value)

    @property
    def _dependencies(self) -> list[Statement]:
        deps: list[Statement] = []
        for filt in self.filters:
            deps.extend(filt._dependencies)
        return deps
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        comp_filter = lambda f: f._compile(vars)
        res = self._type_specifier + "".join(map(comp_filter, self.filters))
        if out_var is not None:
            return res + f"->.{out_var};"
        return res + ";"


class Nodes(Elements):
    """A node query.

    Example:

    >>> all_nodes = Nodes(bounding_box=(50.6,7.0,50.8,7.3))
    >>> cinemas = all_nodes.where(amenity="cinema")
    >>> non_cinemas = all_nodes - cinemas
    >>> print(build(non_cinemas))
    node(50.6,7.0,50.8,7.3)->.set_0;
    (.set_0; - node.set_0["amenity"="cinema"];);
    """

    _type_specifier: str = "node"

class Ways(Elements):
    """A way query."""

    _type_specifier: str = "way"

class Relations(Elements):
    """A relation query."""

    _type_specifier: str = "rel"

class Areas(Elements):
    """An area query."""

    _type_specifier: str = "area"



class Combination(Set):
    """A class from which sets that represent group operations on sets
    must derive from.
    """
    pass


class Union(Combination):
    """
    Represents a union of sets: `(set_1; set_2; …);`

    Example:

    >>> union = Union(Ways(42), Nodes(42))
    >>> print(build(union))
    (way(42); node(42));
    >>> union = Ways(42) + Nodes(42)
    >>> print(build(union))
    (way(42); node(42));
    """
    def __init__(self, *sets: Set, label: str | None = None, filters: Iterable[Filter] = []) -> None:
        """
        Args:
            statements: The list of statement whose results to combine.
        """
        super().__init__(filters, label)
        self.sets = list(sets)
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [*self.sets]
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        substmts = []
        for stmt in self.sets:
            substmts.append(vars.get_or_compile(stmt, ".{};"))
        if out_var is None:
            return f"({' '.join(substmts)});"
        return f"({' '.join(substmts)})->.{out_var};"


class Difference(Combination):
    """
    Represents the difference of two sets: `(set_1 - set_2;);`

    Example:

    >>> bbox_ways = Ways(bounding_box=(50.6,7.0,50.8,7.3))
    >>> one_way = Ways(41)
    >>> print(build(Difference(bbox_ways, one_way)))
    (way(50.6,7.0,50.8,7.3); - way(42););
    >>> print(build(bbox_ways - one_way))
    (way(50.6,7.0,50.8,7.3); - way(42););
    """
    def __init__(self, a: Set, b: Set, label: str | None = None, filters: Iterable[Filter] = []) -> None:
        """
        Args:
            a: The base statement.
            b: The statement whose results to remove from `a`.
        """
        super().__init__(filters, label)
        self.a = a
        self.b = b
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [self.a, self.b]
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        a = vars.get_or_compile(self.a, ".{};")
        b = vars.get_or_compile(self.b, ".{};")
        if out_var is None:
            return f"({a} - {b});"
        return f"({a} - {b})->.{out_var};"