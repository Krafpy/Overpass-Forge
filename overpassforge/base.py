from __future__ import annotations
from typing import Iterable, TYPE_CHECKING
from .filters import (
    Filter,
    BoundingBox,
    Ids,
    Regex,
    Key,
    Intersection,
    Newer,
    Changed,
    User,
    Around,
    Area,
    Pivot,
    Polygon
)
from ._variables import VariableManager as _VariableManager
from datetime import datetime

if TYPE_CHECKING:
    from ._visitors import Visitor as _Visitor
    from .statements import Difference, Union, Areas


OUT_OPTIONS = ("ids", "skel", "body", "tags", "meta", "noids", "geom", "bb", "center", "asc", "qt", "count")

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Statement:
    """Represents a generic Overpass QL statement."""

    def __init__(self, label: str | None = None) -> None:
        """
        Args:
            label: A label for this statement which may be used
                as variable name for the result of this statement at compilation.
        """
        self.out_options: list[set[str]] = []
        self.label = label
    
    def _accept_pre(self, visitor: _Visitor):
        """Calls the appropriate visitor method when this statement is visited before
        visiting it's dependencies.
        """
        visitor.visit_statement_pre(self)

    def _accept_post(self, visitor: _Visitor):
        """Calls the appropriate visitor method after having visited this statement's
        dependencies.
        """
        visitor.visit_statement_post(self)

    def _compile_core(self, vars: _VariableManager, out_var: str | None = None) -> str:
        """Compiles the statement into its Overpass query string, without additional
        output statements.

        Args:
            vars: The variable manager at compile time
            out_var: The name of the output variable where to
                store the result of this statement
        """
        raise NotImplementedError("Must be implemented in subclass.")
    
    @property
    def _dependencies(self) -> list[Statement]:
        """The list of statements on which this statement depends on (readonly)
        """
        raise NotImplementedError("Must be implemented in subclass.")
    
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
            options: None or any combination of "ids", "skel", "body", "tags",
                "meta", "noids", "geom", "bb", "center", "asc", "qt", "count" or
                a bounding box (south,west,north,east).
        
        Returns:
            This same instance.
        
        Raises:
            ValueError: Invalid output options.
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
        
        self.out_options.append(valid_options)
        return self
    
    def _compile(self, vars: _VariableManager, out_var: str | None = None) -> str:
        """Compiles the statement into its Overpass query string, with its eventual outputs.

        Args:
            vars: The variable manager at compile time.
            out_var: The name of the output variable where to store the result
                of this statement.
        
        Returns:
            The compiled statement string.
        """
        compiled = self._compile_core(vars, out_var)
        if len(self.out_options) == 0:
            return compiled
        
        outs = []
        var = vars.get(self)
        for opts in self.out_options:
            out = f".{var} out" if var is not None else "out"
            out += (" " + " ".join(sorted(opts))) if len(opts) > 0 else ""
            out += ";"
            outs.append(out)
        return compiled + "\n" + "\n".join(outs)
    
    def __repr__(self) -> str:
        info = self.label if self.label else id(self)
        return f"<{self.__class__.__name__} \'{info}\'>"


class QueryStatement(Statement):
    """Represents a query statement, e.g. node, rel, way... Query statements always
    return a set that can be used as input to other statements/filters.
    """

    _type_specifier: str = "<Unspecified>"
    
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
        
        super().__init__(label)

        self.filters = list(filters)

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
    
    def filter(self, *filters: Filter) -> QueryStatement:
        """Adds filters to the statement/set.

        Args:
            filters: A list of filters.
        """
        return self.__class__(filters=[Intersection(self), *filters])
    
    def where(self, *keys: str | Regex, **tags: str | Regex) -> QueryStatement:
        """Adds filters "key", ~"key", "key"="value", or "key"~"value".

        Args:
            keys: List of keys the elements must have
            tags: List of key="value" tags the elements must have.
        """

        filters: list[Filter] = [Intersection(self)]
        for key in keys:
            filters.append(Key(key))
        for key, value in tags.items():
            filters.append(Key(key) == value)
        return self.__class__(filters=filters)
    
    def within(self, area: tuple[float,float,float,float] | BoundingBox | Polygon | Area | Areas) -> QueryStatement:
        """Filters the elements that are in the specified area.

        Args:
            area: A bounding box (filter object or as a tuple), polygon filter,
                area filter or set of areas.
        """
        if isinstance(area, Filter):
            return self.__class__(filters=[Intersection(self), area])
        elif isinstance(area, tuple):
            return self.__class__(filters=[Intersection(self), BoundingBox(*area)])
        else:
            return self.__class__(filters=[Intersection(self), Area(area)])
    
    def intersection(self, *others: Statement) -> QueryStatement:
        """Returns the statement computing the intersection of
        this statement with the others.
        
        Args:
            others: Other statements to intersect with
        """
        return self.__class__(filters=[Intersection(self, *others)])
    
    def changed_since(self, date: datetime) -> QueryStatement:
        """Filters the elements that were changed since the specified datetime.

        Args:
            date: The lower bound of change dates to consider
        """
        return self.__class__(filters=[Intersection(self), Newer(date)])
    
    def changed_between(self, lower: datetime, upper: datetime) -> QueryStatement:
        """Filters the elements that were changed between the two specified dates.

        Args:
            lower (datetime): Lower bound datetime.
            upper (datetime): Upper bound datetime.
        """
        return self.__class__(filters=[Intersection(self), Changed(lower, upper)])
    
    def last_changed_by(self, *users: str | int) -> QueryStatement:
        """Filters the elements that last changed by any of the given users.

        Args:
            users: The list of user names or user ids.
        """
        return self.__class__(filters=[Intersection(self), User(*users)])
    
    def outlines_of(self, area: 'Areas') -> QueryStatement:
        """Filters the elements that are part of the outline of the given area.

        Args:
            area: The area to consider to outline of.
        """
        return self.__class__(filters=[Intersection(self), Pivot(area)])
    
    def around(self,
        radius: float,
        other: Statement | None = None,
        lats: Iterable[float] | None = None, 
        lons: Iterable[float] | None = None
    ):
        """Filters elements that are within a given radius of the elements of another set
        or a list of given coordinates (cannot specify both).

        Args:
            radius: The radius to consider around each element (in meters).
            other: Another statement.
            lats: List of latitude of points.
            lons: List of longitudes of points.
        """
        around = Around(radius, other, lats, lons)
        return self.__class__(filters=[Intersection(self), around])

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


class BlockStatement(Statement):
    """Represents a block statement, i.e. a statement which acts on multiple statements."""
    pass