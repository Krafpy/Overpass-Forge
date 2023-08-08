from __future__ import annotations
from .base import Statement, QueryStatement, BlockStatement
from ._variables import VariableManager as _VariableManager
from .errors import UnexpectedCompilationError


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


class Nodes(QueryStatement):
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

class Ways(QueryStatement):
    """A way query."""

    _type_specifier: str = "way"

class Relations(QueryStatement):
    """A relation query."""

    _type_specifier: str = "rel"

class Areas(QueryStatement):
    """An area query."""

    _type_specifier: str = "area"


class Union(BlockStatement):
    """
    Represents a union of statements: `(statement_1; statement_2; …);`

    Example:

    >>> union = Union(Ways(42), Nodes(42))
    >>> print(build(union))
    (way(42); node(42));
    >>> union = Ways(42) + Nodes(42)
    (way(42); node(42));
    """
    def __init__(self, *statements: Statement, label: str | None = None) -> None:
        """
        Args:
            statements: The list of statement whose results to combine.
        """
        super().__init__(label)
        self.statements = list(statements)
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [*self.statements]
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        substmts = []
        for stmt in self.statements:
            substmts.append(vars.get_or_compile(stmt, ".{};"))
        if out_var is None:
            return f"({' '.join(substmts)});"
        return f"({' '.join(substmts)})->.{out_var};"


class Difference(BlockStatement):
    """
    Represents the difference of two statements: `(statement_1 - statement_2;);`

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
    
    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        a = vars.get_or_compile(self.a, ".{};")
        b = vars.get_or_compile(self.b, ".{};")
        if out_var is None:
            return f"({a} - {b});"
        return f"({a} - {b})->.{out_var};"