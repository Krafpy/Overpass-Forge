from __future__ import annotations
from .base import Statement, Set
from ._variables import VariableManager as _VariableManager
from .errors import UnexpectedCompilationError, InvalidStatementAttributes
from .filters import (
    Filter,
    BoundingBox,
    Ids,
    Key,
    Intersect,
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
        self._dependency_dict = dependencies
        if "{}" in raw:
            raise ValueError("All inserted dependencies must be named.")
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        """Compiles the statement into its Overpass query string, without eventual
        outputs.
        """
        var_names: dict[str, str] = {}
        for name, stmt in self._dependency_dict.items():
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
        return list(self._dependency_dict.values())


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
            self._filters.append(Intersect(input_set))

        if isinstance(ids, int):
            self._filters.append(Ids(ids))
        elif ids is not None:
            self._filters.append(Ids(*ids))

        if bounding_box is not None:
            self._filters.append(BoundingBox(*bounding_box))
        
        if within is not None:
            self._filters.append(Area(within))
        
        if isinstance(around, Around):
            self._filters.append(around)
        elif around is not None:
            self._filters.append(Around(around[1], around[0]))
        
        for key, value in tags.items():
            self._filters.append(Key(key) == value)
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        comp_filter = lambda f: f._compile(vars)
        res = self._type_specifier + "".join(map(comp_filter, self._filters))
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
    must derive from (e.g. unions, differences...).
    """

    def __init__(self, label: str | None = None) -> None:
        super().__init__(label=label)

    def filter(self, *filters: Filter) -> Set:
        return Elements(filters=[Intersect(self), *filters])


class Union(Combination):
    """Represents a union of sets: `(set_1; set_2; …);`

    Example:

    >>> union = Union(Ways(42), Nodes(42))
    >>> print(build(union))
    (way(42); node(42));
    >>> union = Ways(42) + Nodes(42)
    >>> print(build(union))
    (way(42); node(42));
    """

    def __init__(self, *statements: Set, label: str | None = None) -> None:
        """
        Args:
            statements: The list of statement whose results to combine.
        """
        super().__init__(label)
        self.statements = list(statements)
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [*self.statements]
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        substmts = []
        for stmt in self.statements:
            substmts.append(vars.get_or_compile(stmt, ".{};"))
        if out_var is None:
            return f"({' '.join(substmts)});"
        return f"({' '.join(substmts)})->.{out_var};"


class Difference(Combination):
    """Represents the difference of two sets: `(set_1 - set_2;);`

    Example:

    >>> bbox_ways = Ways(bounding_box=(50.6,7.0,50.8,7.3))
    >>> one_way = Ways(41)
    >>> print(build(Difference(bbox_ways, one_way)))
    (way(50.6,7.0,50.8,7.3); - way(42););
    >>> print(build(bbox_ways - one_way))
    (way(50.6,7.0,50.8,7.3); - way(42););
    """

    def __init__(self, a: Statement, b: Statement, label: str | None = None) -> None:
        """
        Args:
            a: The base statement.
            b: The statement whose results to remove from `a`.
        """
        super().__init__(label)
        self.a = a
        self.b = b
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [self.a, self.b]
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        a = vars.get_or_compile(self.a, ".{};")
        b = vars.get_or_compile(self.b, ".{};")
        if out_var is None:
            return f"({a} - {b});"
        return f"({a} - {b})->.{out_var};"


class _Recurse(Set):
    """Base class for recurse statements (>, >>, <, <<)."""

    _symbol: str = ""

    def __init__(self, input_set: Statement, label: str | None = None) -> None:
        super().__init__(label=label)
        self.input_set = input_set
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [self.input_set]
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        match vars.is_named(self.input_set), out_var is not None:
            case False, False:
                return f"{self._symbol};"
            case True, False:
                return f".{vars[self.input_set]} {self._symbol};"
            case False, True:
                return f"{self._symbol} ->.{out_var};"
            case _:
                return f".{vars[self.input_set]} {self._symbol} ->.{out_var};"

class RecurseDown(_Recurse):
    """Recurse down elements (``>``).
    Takes an input set and produces a set composed of:
    - all nodes that are part of a way which appears in the input set; plus
    - all nodes and ways that are members of a relation which appears in the
    input set; plus
    - all nodes that are part of a way which appears in the result set.

    (taken from the Overpass QL documentation)
    """
    _symbol = ">"

class RecurseDownRels(_Recurse):
    """Recurse down relations (``>>``).
    Similar to simple recurse down but also it continues to follow the membership
    links including nodes in ways until for every object in its input or result
    set all he members of that object are in the result set as well. 

    (taken from the Overpass QL documentation)
    """
    _symbol = ">>"

class RecurseUp(_Recurse):
    """Recurse up elements (``<``).
    Takes an input set and produces a set composed of:
    - all ways that have a node which appears in the input set; plus
    - all relations that have a node or way which appears in the input set;
    plus
    - all relations that have a way which appears in the result set.

    (taken from the Overpass QL documentation)
    """
    _symbol = "<"

class RecurseUpRels(_Recurse):
    """Recurse up relations (``<<``).
    Similar to simple recurse up but also it continues to follow backlinks onto
    the found relations until it contains all relations that point to an object
    in the input or result set. 

    (taken from the Overpass QL documentation)
    """
    _symbol = "<<"


class OverlappingAreas(Set):
    """Corresponds to the ``is_in`` statement.
    Represents the areas and closed ways that cover:
    - the given coordinates (when specified) or
    - one or more nodes from the input set (when no coordinates are specified).

    (taken from the Overpass QL documentation)
    """

    def __init__(self,
        lat: float | None = None,
        lon: float | None = None,
        input_set: Statement | None = None,
        label: str | None = None
    ) -> None:
        super().__init__(label=label)
        self.input_set = input_set
        self.lat = lat
        self.lon = lon
    
    def filter(self, *filters: Filter) -> Set:
        return Areas(filters=[Intersect(self), *filters])
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [] if self.input_set is None else [self.input_set]
    
    def _compile_statement(self, vars: _VariableManager, out_var: str | None = None) -> str:
        if self.input_set is not None and (self.lat is not None or self.lon is not None):
            raise InvalidStatementAttributes("Cannot use both coordinates and input set.")

        res = "is_in"
        if self.input_set is not None:
            if vars.is_named(self.input_set):
                res = f".{vars[self.input_set]} {res}"
        elif self.lat is not None and self.lon is not None:
            res = f"{res}({self.lat},{self.lon})"
        else:
            raise InvalidStatementAttributes("Input set or coordinates not defined.")

        if out_var is not None:
            return f"{res} ->.{out_var};"
        return f"{res};"