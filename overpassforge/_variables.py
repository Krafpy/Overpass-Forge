from typing import TYPE_CHECKING
from .errors import UnexpectedCompilationError

if TYPE_CHECKING:
    from .base import Statement

class VariableManager:
    def __init__(self):
        self._var_names: dict['Statement', str] = {}
        self._next_id = 0

    def get_or_compile(self, stmt: 'Statement', name_format: str = "{}") -> str:
        if stmt in self._var_names:
            return name_format.format(self._var_names[stmt])
        else:
            return stmt._compile(self)

    def add_statement(self, stmt: 'Statement') -> str:
        if stmt in self._var_names:
            raise UnexpectedCompilationError(f"Trying to name an already named statement.", stmt)
        
        name = f"set_{self._next_id}"
        if stmt.label is not None and stmt.label not in self._var_names.values():
            name = stmt.label
        self._var_names[stmt] = name
        self._next_id += 1
        return name
    
    def is_named(self, stmt: 'Statement') -> bool:
        return stmt in self._var_names

    def __getitem__(self, stmt: 'Statement') -> str:
        return self._var_names[stmt]
    
    def get(self, stmt: 'Statement', if_none=None):
        if stmt in self._var_names:
            return self._var_names[stmt]
        return if_none