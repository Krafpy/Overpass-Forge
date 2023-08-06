from __future__ import annotations
import re
from typing import TYPE_CHECKING, Iterable
from datetime import datetime
from .variables import VariableManager
from .utils import partition

if TYPE_CHECKING:
    from .base import Statement
    from .variables import VariableManager
    from .statements import Areas


class Filter:
    """
    Represents a filter that can be applied on a query statement.
    """
    def __init__(self, raw: str | None = None) -> None:
        self._raw = raw or ""

    def compile(self, vars: VariableManager) -> str:
        """
        Builds the Overpass string of this filter.
        """
        return self._raw
    
    @property
    def dependencies(self) -> list[Statement]:
        return []
    
    def __repr__(self) -> str:
        return f"<Filter \"{self._raw}\">"


class Tag(Filter):
    """
    Represents a generic tag filter (has/exists kv).
    """
    def __init__(self, case_sensitive=True) -> None:
        super().__init__()
        self.case_sensitive = case_sensitive
    
    def _comparator(self) -> str:
        raise NotImplementedError("Must be implemented in subclass.")

    def compile(self, vars: VariableManager):
        if self.case_sensitive:
            return f"[{self._comparator()}]"
        return f"[{self._comparator()},i]"
    
    def __repr__(self) -> str:
        return f"<Tag {self._comparator()}>"

class InvalidRegexError(Exception):
    """Raised on an invalid regular expression."""
    
    def __init__(self, expr: str) -> None:
        super().__init__(f"Invalid regular expression {expr}.")


class KeyExists(Tag):
    """
    Filter ["key"]
    """
    def __init__(self, key: str, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
    
    def _comparator(self) -> str:
        return f"\"{self.key}\""

class KeyNotExists(Tag):
    """
    Filter [!"key"]
    """
    def __init__(self, key: str, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
    
    def _comparator(self) -> str:
        return f"!\"{self.key}\""

class KeyEqualsValue(Tag):
    """
    Filter ["key"="value"]
    """
    def __init__(self, key: str, value: str, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
        self.value = value
    
    def _comparator(self) -> str:
        return f"\"{self.key}\"=\"{self.value}\""

class KeyNotEqualsValue(Tag):
    """
    Filter ["key"!="value"]
    """
    def __init__(self, key: str, value: str, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
        self.value = value
    
    def _comparator(self) -> str:
        return f"\"{self.key}\"!=\"{self.value}\""

class ValueMatchesExpr(Tag):
    """
    Filter ["key"~"value_pattern"]
    """
    def __init__(self, key: str, pattern: str, check_pattern_on_compile=True, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
        self.pattern = pattern
        self.check_pattern_on_compile = check_pattern_on_compile
    
    def _comparator(self) -> str:
        if self.check_pattern_on_compile:
            try:
                re.compile(self.pattern)
            except re.error:
                raise InvalidRegexError(self.pattern)
        return f"\"{self.key}\"~\"{self.pattern}\""

class ValueNotMatchesExpr(Tag):
    """
    Filter ["key"!~"value_pattern"]
    """
    def __init__(self, key: str, pattern: str, check_pattern_on_compile=True, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key = key
        self.pattern = pattern
        self.check_pattern_on_compile = check_pattern_on_compile
    
    def _comparator(self) -> str:
        if self.check_pattern_on_compile:
            try:
                re.compile(self.pattern)
            except re.error:
                raise InvalidRegexError(self.pattern)
        return f"\"{self.key}\"!~\"{self.pattern}\""

class KeyValueMatchExprs(Tag):
    """
    Filter [~"key_pattern"~"value_pattern"]
    """
    def __init__(self, key_pattern: str, value_pattern: str, check_pattern_on_compile=True, case_sensitive=True) -> None:
        super().__init__(case_sensitive)
        self.key_pattern = key_pattern
        self.value_pattern = value_pattern
        self.check_pattern_on_compile = check_pattern_on_compile
    
    def _comparator(self) -> str:
        if self.check_pattern_on_compile:
            try:
                re.compile(self.key_pattern)
            except re.error:
                raise InvalidRegexError(self.key_pattern)
            try:
                re.compile(self.value_pattern)
            except re.error:
                raise InvalidRegexError(self.value_pattern)
        return f"~\"{self.key_pattern}\"~\"{self.value_pattern}\""



class BoundingBox(Filter):
    """
    Bounding box filter on a query statement.
    """

    def __init__(self, south: float, west: float, north: float, east: float) -> None:
        """
        Args:
            south, west, north, east (float): bounding box latitudes and longitudes
        """
        super().__init__()

        self.south = south
        self.west = west
        self.north = north
        self.east = east
    
    def compile(self, vars: VariableManager) -> str:
        return f"({self.south},{self.west},{self.north},{self.east})"
    
    def __repr__(self) -> str:
        return f"<BoundingBox ({self.south},{self.west},{self.north},{self.east})>"


class Ids(Filter):
    """
    Represents an id filter.
    """

    def __init__(self, *ids: int) -> None:
        """
        Args:
            ids (int): the list of OSM ids to filter
        """
        super().__init__()
        
        self.ids = ids
    
    def compile(self, vars: VariableManager) -> str:
        match len(self.ids):
            case 0:
                return ""
            case 1:
                return f"({self.ids[0]})"
            case _:
                return f"(id:{','.join(map(str, self.ids))})"
    
    def __repr__(self) -> str:
        return f"<Ids ({self.ids})>"


class Intersection(Filter):
    """
    Intersection with other sets.
    """
    def __init__(self, *elements: Statement) -> None:
        super().__init__()
        self.statements = list(elements)
    
    @property
    def dependencies(self) -> list[Statement]:
        return [*self.statements]
    
    def compile(self, vars: VariableManager) -> str:
        if len(self.statements) == 0:
            raise RuntimeError("Empty intersection.")
        names: list[str] = []
        for stmt in self.statements:
            names.append(vars[stmt])
        return "." + ".".join(names)
    
    def __repr__(self) -> str:
        return f"<IntersectsWith {', '.join(map(str, self.statements))}>"


class Newer(Filter):
    """
    Filter by newer change dates.
    """
    def __init__(self, date: datetime):
        self.date = date
    
    def compile(self, vars: VariableManager) -> str:
        from .base import DATE_FORMAT
        return f"(newer:\"{self.date.strftime(DATE_FORMAT)}\")"
    
    def __repr__(self) -> str:
        return f"<Newer {self.date}>"

class Changed(Filter):
    """
    Filter that selects elements that have been changed between two given
    dates. If only the lower date is given, the second is assumed to be the
    front date of the database.
    """
    def __init__(self, lower: datetime, higher: datetime | None = None):
        self.lower = lower
        self.higher = higher
    
    def compile(self, vars: VariableManager) -> str:
        from .base import DATE_FORMAT
        if self.higher is None:
            return f"(changed:\"{self.lower.strftime(DATE_FORMAT)}\")"
        return f"(changed:\"{self.lower.strftime(DATE_FORMAT)}\",\"{self.higher.strftime(DATE_FORMAT)}\")"
    
    def __repr__(self) -> str:
        return f"<Changed {self.lower} - {self.higher}>"

class User(Filter):
    """
    Filter the elements last edited by the specified users.
    """
    def __init__(self, *users: int | str) -> None:
        """
        Args:
            *users: a list of user names or user ids.
        """
        if len(users) == 0:
            raise ValueError("Must list at least one user.")
        self.users = users

    def compile(self, vars: VariableManager) -> str:
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
    """
    Filters the elements which are within the given area.
    """
    def __init__(self, input_area: 'Areas') -> None:
        self.input_area = input_area
    
    @property
    def dependencies(self) -> list[Statement]:
        return [self.input_area]
    
    def compile(self, vars: VariableManager) -> str:
        return f"(area.{vars[self.input_area]})"

class Pivot(Filter):
    """
    Filters the elements which are part of the outline of the given
    area.
    """
    def __init__(self, input_area: 'Areas') -> None:
        self.input_area = input_area
    
    @property
    def dependencies(self) -> list[Statement]:
        return [self.input_area]
    
    def compile(self, vars: VariableManager) -> str:
        return f"(pivot.{vars[self.input_area]})"


class Around(Filter):
    """
    Filters elements within a certain radius around elements in the
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
        Creates an around filter.

        Args:
            radius (float): the radius in meters around each elements
            input_set (Statement): the input set of elements around which to filter
            (cannot be used in combination with lats, lons)
            lats, lons: latitude and longitudes of points around which to filter
            (cannot be used in combination with input_set)
        """
        self.radius = radius
        self.input_set = input_set
        self.lats = lats
        self.lons = lons
    
    @property
    def dependencies(self) -> list[Statement]:
        if self.input_set is None:
            return []
        return [self.input_set]
    
    def compile(self, vars: VariableManager) -> str:
        if self.input_set is not None and (self.lats is not None or self.lons is not None):
            raise AttributeError("Cannot use both coordinates and input set.")
        
        if self.input_set is not None:
            return f"(around.{vars[self.input_set]}:{self.radius})"
        if self.lats is not None and self.lons is not None:
            latlons = []
            for lat, lon in zip(self.lats, self.lons):
                latlons.append(str(lat))
                latlons.append(str(lon))
            return f"(around:{self.radius},{','.join(latlons)})"
        
        raise AttributeError("Input set or coordinates not defined.")