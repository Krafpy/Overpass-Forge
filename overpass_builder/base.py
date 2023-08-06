from __future__ import annotations
from typing import Iterable, TYPE_CHECKING
from .filters import (
    Filter,
    BoundingBox,
    Ids,
    KeyEqualsValue,
    IntersectsWith,
    Newer,
    Changed,
    User,
    Around,
    InArea,
    Pivot
)
from .variables import VariableManager
from datetime import datetime

if TYPE_CHECKING:
    from .visitors import Visitor
    from .statements import Difference, Union, Areas


OUT_OPTIONS = ("ids", "skel", "body", "tags", "meta", "noids", "geom", "bb", "center", "asc", "qt", "count")

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Statement:
    """
    Represents a generic Overpass QL statement.
    """

    def __init__(self, raw: str = "", **dependencies: Statement) -> None:
        """
        Raw Overpass query string. It can be formated to support dependency
        from other statements (raw or not). Placholders will be replaced
        by the names of the variables where the dependencies output their
        results.

        Args:
            raw (str): A formatable string of the query. Named placeholders
            (e.g. "{name}") indicating dependency on other statements. An
            optional special {:out_var} placeholder indicates where the name of
            the output set must be placed.
            **dependencies (Statement): the list of named statement on which
            this statements depends on. The names must match the placeholders
            in the raw query.
        
        Example:
            ```python
            >>> foo = Nodes().where(name="Foo")
            >>> bar = Statement("node.{x}[amenity=\"bar\"]->.{:out_var};", x=foo)
            >>> baz = Nodes(input_set=bar).within((50.6,7.0,50.8,7.3))
            >>> print(build(baz))
                node["name"="Foo"]->.set_0;
                node.set_0[amenity="bar"]->.set_1;
                node.set_1(50.6,7.0,50.8,7.3);
            ```
        """
        self._raw = raw
        self._dependencies = dependencies
        if "{}" in raw:
            raise ValueError("All inserted dependencies must be named.")
        for name in dependencies.keys():
            if "{" + name + "}" not in raw:
                raise ValueError(f"Unused dependency {name}.")
        
        self.out_options: set[str] | None = None
        self.label: str | None = None
    
    def accept_pre(self, visitor: Visitor):
        """
        Calls the appropriate visitor method when this statement is visited before
        visiting it's dependencies.
        """
        visitor.visit_statement_pre(self)

    def accept_post(self, visitor: Visitor):
        """
        Calls the appropriate visitor method after having visited this statement's
        dependencies.
        """
        visitor.visit_statement_post(self)

    def _compile(self, vars: VariableManager, out_var: str | None = None) -> str:
        """
        Compiles the statement into its Overpass query string.
        """
        var_names: dict[str, str] = {}
        for name, stmt in self._dependencies.items():
            if not vars.is_named(stmt):
                raise RuntimeError("All inserted sets must use variables.")
            var_names[name] = vars[stmt]
        compiled = self._raw
        if "{:out_var}" in self._raw:
            compiled = compiled.replace("{:out_var}", out_var or "._")
        elif out_var is not None:
            raise RuntimeError("No output variable specified.")
        return compiled.format(**var_names)
    
    @property
    def dependencies(self) -> list[Statement]:
        """
        The list of statements on which this statement depends on.
        """
        return list(self._dependencies.values())
    
    def __hash__(self) -> int:
        return id(self)
    
    def __sub__(self, other: Statement) -> Difference:
        from .statements import Difference
        return Difference(self, other)
    
    def __add__(self, other: Statement) -> Union:
        from .statements import Union
        return Union(self, other)
    
    def out(self, *options: str | tuple[float, float, float, float]) -> Statement:
        """
        Indicate that the result of this statement must be outputed.

        Args:
            options: one or a combination of "ids", "skel", "body", "tags",
            "meta", "noids", "geom", "bb", "center", "asc", "qt", "count" or
            a bounding box (south,west,north,east)
        
        Returns: itself
        """
        extract = lambda item: item.strip().split(' ')
        valid_options: set[str] = set()
        for item in options:
            if isinstance(item, str):
                opts = set(filter(lambda opt: len(opt) > 0, extract(item)))
                invalid = opts - set(OUT_OPTIONS)
                if len(invalid) > 0:
                    raise ValueError(f"Invalid out options: {','.join(invalid)}")
                valid_options.update(opts)
            else:
                valid_options.add(str(item))
        
        self.out_options = valid_options
        return self
    
    def compile(self, vars: VariableManager, out_var: str | None = None) -> str:
        compiled = self._compile(vars, out_var)
        if self.out_options is None:
            return compiled
        var = vars.get(self)
        opts = self.out_options
        out = f".{var} out" if var is not None else "out"
        out += (" " + " ".join(sorted(opts))) if len(opts) > 0 else ""
        out += ";"
        return compiled + "\n" + out
    
    def __repr__(self) -> str:
        info = self.label if self.label else id(self)
        return f"<{self.__class__.__name__} \'{info}\'>"

class QueryStatement(Statement):
    """
    Represents a query statement, e.g. node, rel, way... Query statements always
    return a set that can be used as input to other statements/filters.
    """

    _type_specifier: str = "<Unspecified>"
    
    def __init__(self, *,
        ids: Iterable[int] | int | None = None,
        bounding_box: tuple[float, float, float, float] | None = None,
        input_set: Statement | None = None,
        within: Areas | None = None,
        around: tuple[Statement, float] | None = None,
        filters: Iterable[Filter] = [],
        **tags: str
    ) -> None:
        
        super().__init__()

        self.filters = list(filters)

        if isinstance(input_set, Statement):
            self.filters.append(IntersectsWith(input_set))

        if isinstance(ids, int):
            self.filters.append(Ids(ids))
        elif ids is not None:
            self.filters.append(Ids(*ids))

        if bounding_box is not None:
            self.filters.append(BoundingBox(*bounding_box))
        
        if within is not None:
            self.filters.append(InArea(within))
        
        if around is not None:
            self.filters.append(Around(around[1], around[0]))
        
        for key, value in tags.items():
            self.filters.append(KeyEqualsValue(key, value))
    
    def filter(self, *args: Filter) -> QueryStatement:
        """
        Adds filters to the statement/set.
        """
        return self.__class__(filters=[IntersectsWith(self), *args])
    
    def where(self, **tags: str) -> QueryStatement:
        """
        Adds filters "key"="value" on tags.
        """
        filters: list[Filter] = [IntersectsWith(self)]
        for k, v in tags.items():
            filters.append(KeyEqualsValue(k, v))
        return self.__class__(filters=filters)
    
    def within(self, area: tuple[float,float,float,float] | BoundingBox | 'Areas') -> QueryStatement:
        """
        Filters the elements that are in the specified area.
        """
        if isinstance(area, BoundingBox):
            return self.__class__(filters=[IntersectsWith(self), area])
        elif isinstance(area, tuple):
            return self.__class__(filters=[IntersectsWith(self), BoundingBox(*area)])
        else:
            return self.__class__(filters=[IntersectsWith(self), InArea(area)])
    
    def intersection(self, *others: Statement) -> QueryStatement:
        """
        Returns the statement computing the intersection of
        this set with the others.
        """
        return self.__class__(filters=[IntersectsWith(self, *others)])
    
    def changed_since(self, date: datetime) -> QueryStatement:
        """
        Filters the elements that were changed since the specified datetime.
        """
        return self.__class__(filters=[IntersectsWith(self), Newer(date)])
    
    def changed_between(self, lower: datetime, higher: datetime) -> QueryStatement:
        """
        Filters the elements that were changed between the two specified dates.
        """
        return self.__class__(filters=[IntersectsWith(self), Changed(lower, higher)])
    
    def last_changed_by(self, *users: str | int) -> QueryStatement:
        """
        Filters the elements that last changed by any of the given users.

        Args:
            *users: the list of user names or user ids
        """
        return self.__class__(filters=[IntersectsWith(self), User(*users)])
    
    def outlines_of(self, area: 'Areas') -> QueryStatement:
        """
        Filters the elements that are part of the outline of the given area.
        """
        return self.__class__(filters=[IntersectsWith(self), Pivot(area)])
    
    def around(self,
        radius: float,
        other: Statement | None,
        lats: Iterable[float] | None = None, 
        lons: Iterable[float] | None = None
    ):
        """
        Filters elements that are within a given radius of the elements of another set
        or a list of given coordinates (cannot specify both).
        """
        around = Around(radius, other, lats, lons)
        return self.__class__(filters=[IntersectsWith(self), around])

    @property
    def dependencies(self) -> list[Statement]:
        deps: list[Statement] = []
        for filt in self.filters:
            deps.extend(filt.dependencies)
        return deps
    
    def _compile(self, vars: VariableManager, out_var: str | None = None) -> str:
        comp_filter = lambda f: f.compile(vars)
        res = self._type_specifier + "".join(map(comp_filter, self.filters))
        if out_var is not None:
            return res + f"->.{out_var};"
        return res + ";"


class BlockStatement(Statement):
    pass