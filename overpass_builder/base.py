from __future__ import annotations
from typing import Iterable, TYPE_CHECKING
from .filters import Filter, BoundingBox, Ids, KeyEqualsValue, IntersectsWith, Newer
from .variables import VariableManager
from datetime import datetime

if TYPE_CHECKING:
    from .visitors import Visitor
    from .statements import Difference, Union


OUT_OPTIONS = ("ids", "skel", "body", "tags", "meta", "noids", "geom", "bb", "center", "asc", "qt", "count")

DATE_FORMAT = "%Y-%d-%mT%H:%M:%SZ"


class Statement:
    """
    Represents a generic Overpass QL statement.
    """

    def __init__(self, raw: str = "", **dependencies: Statement) -> None:
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

    def compile(self, vars: VariableManager, out_var: str | None = None) -> str:
        """
        Compiles the statement.
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
            a bounding box (south,east,west,north)
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
    
    def __repr__(self) -> str:
        if self.label is not None:
            return f"<{self.__class__.__name__} \'{self.label}\'>"
        else:
            return f"<{self.__class__.__name__} {id(self)}>"

class QueryStatement(Statement):
    """
    Represents a query statement, e.g. node, rel, way...
    """

    _type_specifier: str = "<Unspecified>"
    
    def __init__(self, *,
        ids: Ids | Iterable[int] | int | None = None,
        bounding_box: BoundingBox | tuple[float, float, float, float] | None = None,
        input_set: Statement | None = None,
        filters: Iterable[Filter] = [],
    ) -> None:
        
        super().__init__()

        self.filters = list(filters)

        if isinstance(ids, Ids):
            self.filters.append(ids)
        elif isinstance(ids, int):
            self.filters.append(Ids(ids))
        elif ids is not None:
            self.filters.append(Ids(*ids))

        if isinstance(bounding_box, BoundingBox):
            self.filters.append(bounding_box)
        elif isinstance(bounding_box, tuple):
            self.filters.append(BoundingBox(*bounding_box))
        
        if isinstance(input_set, Statement):
            self.filters.append(IntersectsWith(input_set))
    
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
    
    def within(self, arg: tuple[float,float,float,float] | BoundingBox) -> QueryStatement:
        """
        Filters the elements that are in the specified area.
        """
        bbox = arg if isinstance(arg, BoundingBox) else BoundingBox(*arg)
        return self.__class__(filters=[IntersectsWith(self), bbox])
    
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

    @property
    def dependencies(self) -> list[Statement]:
        deps: list[Statement] = []
        for filt in self.filters:
            deps.extend(filt.dependencies)
        return deps
    
    def compile(self, vars: VariableManager, out_var: str | None = None) -> str:
        comp_filter = lambda f: f.compile(vars)
        res = self._type_specifier + "".join(map(comp_filter, self.filters))
        if out_var is not None:
            return res + f"->.{out_var};"
        return res + ";"


class BlockStatement(Statement):
    pass