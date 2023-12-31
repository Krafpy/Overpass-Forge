from __future__ import annotations
from typing import TYPE_CHECKING, Iterable
from datetime import datetime
from ._variables import VariableManager as _VariableManager
from ._utils import partition
from .errors import InvalidFilterAttributes

if TYPE_CHECKING:
    from .base import Statement
    from .statements import Areas


class Filter:
    """
    Represents a generic filter that can be applied on a query statement.
    """
    def __init__(self, raw: str | None = None) -> None:
        self._raw = raw or ""

    def _compile(self, vars: _VariableManager) -> str:
        """
        Builds the Overpass string of this filter.
        """
        return self._raw
    
    @property
    def _dependencies(self) -> list[Statement]:
        return []
    
    @staticmethod
    def _make(filter: Filter | str):
        return Filter(filter) if isinstance(filter, str) else filter
    
    def __repr__(self) -> str:
        return f"<Filter \"{self._raw}\">"



class Regex:
    """Wrapper around a string to indicate it should be treated as a regex."""

    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
    
    def __str__(self) -> str:
        return self.pattern
    
    def __repr__(self) -> str:
        return f"<Regex \"{self.pattern}\">"

class Tag(Filter):
    """Represents a generic tag filter."""

    def __init__(self, comparison: str, case_sensitive=True):
        """
        Args:
            comparison: the comparison expression string of the tag filter
                (e.g. "name"="Foo", !"tourism")
            case_sensitive: ignore case (e.g. if comparison is "name"="Foo"
                then a tag "name"="fOO" is also valid)
        """
        self.comparison = comparison
        self.case_sensitive = case_sensitive
    
    def _compile(self, vars: _VariableManager) -> str:
        return f"[{self.__str__()}]"
    
    def __str__(self) -> str:
        ending = "" if self.case_sensitive else ",i"
        return f"{self.comparison}{ending}"
    
    def __repr__(self) -> str:
        return f"<Tag {self.comparison}, case={self.case_sensitive}>"

class Key(Tag):
    """
    Represents a key of an element's tags. Used to build tag filter expressions.

    Examples:

    >>> Key("amenity")
    <Tag "amenity", case=True>
    >>> ~Key("amenity")
    <Tag !"amenity", case=True>
    >>> Key("amenity") == "cinema"
    <Tag "amenity"="cinema", case=True>
    >>> Key("name", case_sensitive=False) == Regex("^Foo$")
    <Tag "name"~"^Foo$", case=False>
    >>> Key(Regex("^addr:.*$")) != Regex("^Foo$")
    <Tag ~"^addr:.*$"!~"^Foo$", case=True>
    """

    def __init__(self, key: str | Regex, case_sensitive=True):
        """
        Args:
            key: The key string.
        """
        if isinstance(key, Regex):
            super().__init__(f"~\"{key}\"", case_sensitive)
        else:
            super().__init__(f"\"{key}\"",  case_sensitive)
    
    def __eq__(self, value: str | Regex) -> Tag:
        case = self.case_sensitive
        if isinstance(value, Regex):
            return Tag(f"{self.comparison}~\"{value}\"", case)
        return Tag(f"{self.comparison}=\"{value}\"", case)
    
    def __ne__(self, value: str | Regex) -> Tag:
        case = self.case_sensitive
        if isinstance(value, Regex):
            return Tag(f"{self.comparison}!~\"{value}\"", case)
        return Tag(f"{self.comparison}!=\"{value}\"", case)
    
    def __invert__(self) -> Tag:
        return Tag(f"!{self.comparison}", self.case_sensitive)


class BoundingBox(Filter):
    """
    Bounding box filter on a query statement.
    """

    def __init__(self, south: float, west: float, north: float, east: float) -> None:
        """
        Args:
            south: Minimum latitude.
            west: Minimum longitude.
            north: Maximum latitude.
            east: Maximum longitude.
        """
        super().__init__()

        self.south = south
        self.west = west
        self.north = north
        self.east = east
    
    def _compile(self, vars: _VariableManager) -> str:
        return f"({self.south},{self.west},{self.north},{self.east})"
    
    def __repr__(self) -> str:
        return f"<BoundingBox ({self.south},{self.west},{self.north},{self.east})>"


class Ids(Filter):
    """Represents an id filter."""

    def __init__(self, *ids: int) -> None:
        """
        Args:
            ids: The list of OSM ids to select.
        """
        super().__init__()
        
        self.ids = ids
    
    def _compile(self, vars: _VariableManager) -> str:
        match len(self.ids):
            case 0:
                return ""
            case 1:
                return f"({self.ids[0]})"
            case _:
                return f"(id:{','.join(map(str, self.ids))})"
    
    def __repr__(self) -> str:
        return f"<Ids ({self.ids})>"


class Intersect(Filter):
    """Intersection with other statement results."""

    def __init__(self, *statements: Statement) -> None:
        """
        Args:
            statements: The other statement whose results intersect with.
        """

        super().__init__()
        self.statements = list(statements)
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [*self.statements]
    
    def _compile(self, vars: _VariableManager) -> str:
        if len(self.statements) == 0:
            raise InvalidFilterAttributes("Empty intersection.")
        names: list[str] = []
        for stmt in self.statements:
            names.append(vars[stmt])
        return "." + ".".join(names)
    
    def __repr__(self) -> str:
        return f"<Intersect {', '.join(map(str, self.statements))}>"


class Newer(Filter):
    """Filter by newer change dates."""

    def __init__(self, date: datetime):
        """
        Args:
            date: The oldest when the element has been modified.
        """
        self.date = date
    
    def _compile(self, vars: _VariableManager) -> str:
        from .base import DATE_FORMAT
        return f"(newer:\"{self.date.strftime(DATE_FORMAT)}\")"
    
    def __repr__(self) -> str:
        return f"<Newer {self.date}>"

class Changed(Filter):
    """Filter that selects elements that have been changed between two given
    dates. If only the lower date is given, the second is assumed to be the
    front date of the database.
    """

    def __init__(self, lower: datetime, upper: datetime | None = None):
        """
        Args:
            lower: Dates' range lower bound.
            upper: Dates' range upper bound. If not given, it is assumed to be the
                front date of the database.
        """
        self.lower = lower
        self.upper = upper
    
    def _compile(self, vars: _VariableManager) -> str:
        from .base import DATE_FORMAT
        if self.upper is None:
            return f"(changed:\"{self.lower.strftime(DATE_FORMAT)}\")"
        return f"(changed:\"{self.lower.strftime(DATE_FORMAT)}\",\"{self.upper.strftime(DATE_FORMAT)}\")"
    
    def __repr__(self) -> str:
        return f"<Changed {self.lower} - {self.upper}>"

class User(Filter):
    """Filter the elements last edited by the specified users."""

    def __init__(self, *users: int | str) -> None:
        """
        Args:
            users: A list of user names or user ids.
        
        Raises:
            ValueError: No user specified.
        """
        self.users = users

    def _compile(self, vars: _VariableManager) -> str:
        ids, names = partition(lambda x: isinstance(x, int), self.users)
        ids = list(map(str, ids))
        names = list(map(lambda x: f"\"{x}\"", names))
        
        compiled = ""
        if len(ids) > 0:
            compiled += f"(uid:{','.join(ids)})"
        if len(names) > 0:
            compiled += f"(user:{','.join(names)})"
        return compiled


class Area(Filter):
    """Filters the elements which are within the given area."""

    def __init__(self, input_area: 'Areas') -> None:
        """
        Args:
            input_area: The areas in which the elements must lay in.
        """
        self.input_area = input_area
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [self.input_area]
    
    def _compile(self, vars: _VariableManager) -> str:
        return f"(area.{vars[self.input_area]})"

class Pivot(Filter):
    """Filters the elements which are part of the outline of the given area."""

    def __init__(self, input_area: 'Areas') -> None:
        """
        Args:
            input_area: The areas to consider the outlines of.
        """
        self.input_area = input_area
    
    @property
    def _dependencies(self) -> list[Statement]:
        return [self.input_area]
    
    def _compile(self, vars: _VariableManager) -> str:
        return f"(pivot.{vars[self.input_area]})"


class Around(Filter):
    """Filters elements within a certain radius around elements in the
    input set.
    """

    def __init__(
        self,
        radius: float,
        input_set: Statement | None = None,
        lats: Iterable[float] | None = None,
        lons: Iterable[float] | None = None,
    ):
        """
        Args:
            radius: The radius in meters around each elements.
            input_set: The input set of elements around which to filter
                (cannot be used in combination with lats, lons).
            lats, lons: Latitude and longitudes of points around which to filter
                (cannot be used in combination with input_set).
        """
        self.radius = radius
        self.input_set = input_set
        self.lats = None if lats is None else list(lats)
        self.lons = None if lons is None else list(lons)
    
    @property
    def _dependencies(self) -> list[Statement]:
        if self.input_set is None:
            return []
        return [self.input_set]
    
    def _compile(self, vars: _VariableManager) -> str:
        if self.input_set is not None and (self.lats is not None or self.lons is not None):
            raise InvalidFilterAttributes("Cannot use both coordinates and input set.")
        
        if self.input_set is not None:
            return f"(around.{vars[self.input_set]}:{self.radius})"
        if self.lats is not None and self.lons is not None:
            latlons = []
            for lat, lon in zip(self.lats, self.lons):
                latlons.append(str(lat))
                latlons.append(str(lon))
            return f"(around:{self.radius},{','.join(latlons)})"
        
        raise InvalidFilterAttributes("Input set or coordinates not defined.")

class Polygon(Filter):
    """Filters all elements that are inside the defined polygon."""

    def __init__(self, lats: Iterable[float], lons: Iterable[float]) -> None:
        """
        Args:
            lats: Latitudes of the points describing the polygon.
            lons: Longitudes of the points describing the polygon.
        """
        super().__init__()
        self.lats = lats
        self.lons = lons
    
    def _compile(self, vars: _VariableManager) -> str:
        latlons = []
        for lat, lon in zip(self.lats, self.lons):
            latlons.append(str(lat))
            latlons.append(str(lon))
        return f"(poly:\"{' '.join(latlons)}\")"