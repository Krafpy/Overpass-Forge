from __future__ import annotations
from typing import Iterable, TYPE_CHECKING
from .filters import (
    Filter,
    BoundingBox,
    Regex,
    Key,
    Intersect,
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
    from .statements import (
        Difference,
        Union,
        Areas,
        RecurseDown,
        RecurseDownRels,
        RecurseUp,
        RecurseUpRels
    )


OUT_OPTIONS = ("ids", "skel", "body", "tags", "meta", "noids", "geom", "bb", "center", "asc", "qt", "count")

DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class Statement:
    """Represents a generic Overpass QL statement."""

    def __init__(self, label: str | None = None) -> None:
        """
        Args:
            label: A label for this statement which may be used
                as variable name for the result of this statement at
                compilation.
        """
        self.label = label
    
    def _accept_pre(self, visitor: _Visitor):
        """Calls the appropriate visitor method when this statement is
        visited before visiting it's dependencies.
        """
        visitor.visit_statement_pre(self)

    def _accept_post(self, visitor: _Visitor):
        """Calls the appropriate visitor method after having visited
        this statement's dependencies.
        """
        visitor.visit_statement_post(self)
    
    @property
    def _dependencies(self) -> list[Statement]:
        """The list of statements on which this statement depends on (readonly)
        """
        raise NotImplementedError("Must be implemented in subclass.")
    
    def __hash__(self) -> int:
        return id(self)
    
    def _compile(self, vars: _VariableManager) -> str:
        """Compiles the statement into its Overpass query string.

        Args:
            vars: The variable manager at compile time.
            out_var: The name of the output variable where to store the result
                of this statement.
        
        Returns:
            The compiled statement string.
        """
        raise NotImplementedError("Must be implemented in subclass.")
    
    def __repr__(self) -> str:
        info = self.label if self.label else id(self)
        return f"<{self.__class__.__name__} \'{info}\'>"


class Set(Statement):
    """Represents a set, i.e. a statement that always returns a set of elements."""

    def __init__(self, filters: Iterable[Filter] = [], label: str | None = None) -> None:
        super().__init__(label)

        self._filters = list(filters)
        self.out_options: list[set[str]] = []
    
    def out(self, *options: str | tuple[float, float, float, float]):
        """
        Indicate that this set must be outputed.

        Args:
            options: empty or any combination of "ids", "skel", "body", "tags",
                "meta", "noids", "geom", "bb", "center", "asc", "qt", "count" or
                a bounding box (south,west,north,east).
        
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
    
    def _output(self, vars: _VariableManager) -> str:
        outs = []
        var = vars.get(self)
        base = f".{var} out" if var is not None else "out"
        for opts in self.out_options:
            out = base
            if len(opts) > 0:
                out += " " + " ".join(sorted(opts))
            out += ";"
            outs.append(out)
        return "\n".join(outs)
    
    @property
    def _dependencies(self) -> list[Statement]:
        deps: list[Statement] = []
        for filt in self._filters:
            deps.extend(filt._dependencies)
        return deps
    
    def __sub__(self, other: Set) -> Difference:
        from .statements import Difference
        return Difference(self, other)
    
    def __add__(self, other: Set) -> Union:
        from .statements import Union
        return Union(self, other)

    def __mul__(self, other: Set) -> Set:
        return self.intersection(other)
    
    def filter(self, *filters: Filter | str) -> Set:
        """Adds filters to the set.

        Args:
            filters: A list of filters or strings representing raw
                filters.
        """
        return self.__class__(filters=[Intersect(self), *map(Filter._make, filters)])
    
    def where(self, *keys: str | Regex, **tags: str | Regex) -> Set:
        """Adds filters "key", ~"key", "key"="value", or "key"~"value".

        Args:
            keys: List of keys the elements must have
            tags: List of key="value" tags the elements must have.
        """

        filters: list[Filter] = []
        for key in keys:
            filters.append(Key(key))
        for key, value in tags.items():
            filters.append(Key(key) == value)
        return self.filter(*filters)
    
    def within(self, area: tuple[float,float,float,float] | BoundingBox | Polygon | Area | Areas) -> Set:
        """Filters the elements that are in the specified area.

        Args:
            area: A bounding box (filter object or as a tuple), polygon filter,
                area filter or set of areas.
        """
        if isinstance(area, Filter):
            return self.filter(area)
        elif isinstance(area, tuple):
            return self.filter(BoundingBox(*area))
        else:
            return self.filter(Area(area))
    
    def intersection(self, *others: Statement) -> Set:
        """Returns the statement computing the intersection of
        this statement with the others.
        
        Args:
            others: Other statements to intersect with
        """
        return self.filter(Intersect(*others))
    
    def changed_since(self, date: datetime) -> Set:
        """Filters the elements that were changed since the specified datetime.

        Args:
            date: The lower bound of change dates to consider
        """
        return self.filter(Newer(date))
    
    def changed_between(self, lower: datetime, upper: datetime) -> Set:
        """Filters the elements that were changed between the two specified dates.

        Args:
            lower (datetime): Lower bound datetime.
            upper (datetime): Upper bound datetime.
        """
        return self.filter(Changed(lower, upper))
    
    def last_changed_by(self, *users: str | int) -> Set:
        """Filters the elements that last changed by any of the given users.

        Args:
            users: The list of user names or user ids.
        """
        return self.filter(User(*users))
    
    def outlines_of(self, area: 'Areas') -> Set:
        """Filters the elements that are part of the outline of the given area.

        Args:
            area: The area to consider to outline of.
        """
        return self.filter(Pivot(area))
    
    def around(self,
        radius: float,
        other: Statement | None = None,
        lats: Iterable[float] | None = None, 
        lons: Iterable[float] | None = None
    ) -> Set:
        """Filters elements that are within a given radius of the elements of another set
        or a list of given coordinates (cannot specify both).

        Args:
            radius: The radius to consider around each element (in meters).
            other: Another statement.
            lats: List of latitude of points.
            lons: List of longitudes of points.
        """
        return self.filter(Around(radius, other, lats, lons))

    def recursed_down(self) -> 'RecurseDown':
        """Returns the recursed down (``>``) set."""
        from .statements import RecurseDown
        return RecurseDown(self)

    def recursed_down_rels(self) -> 'RecurseDownRels':
        """Returns the recursed down relations (``>>``) set."""
        from .statements import RecurseDownRels
        return RecurseDownRels(self)
    
    def recursed_up(self) -> 'RecurseUp':
        """Returns the recursed down (``<``) set."""
        from .statements import RecurseUp
        return RecurseUp(self)
    
    def recursed_up_rels(self) -> 'RecurseUpRels':
        """Returns the recursed up relations (``<<``) set."""
        from .statements import RecurseUpRels
        return RecurseUpRels(self)

    def overlapping_areas(self) -> 'Areas':
        """Returns the set of areas that overlap at least one of the elements
        of this set.
        """
        from .statements import OverlappingAreas
        return OverlappingAreas(input_set=self)