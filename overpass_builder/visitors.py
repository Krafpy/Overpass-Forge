from __future__ import annotations
from .statements import Statement
from .variables import VariableManager
from .base import QueryStatement
from .utils import partition
from .filters import Filter, IntersectsWith
from dataclasses import dataclass


class Visitor:
    def visit_statement_pre(self, statement: Statement):
        pass
    
    def visit_statement_post(self, statement: Statement):
        pass


class CircularDependencyError(Exception):
    pass

class CycleDetector(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.visiting: dict[Statement, bool] = {}
    
    def visit_statement_pre(self, statement: Statement):
        if statement not in self.visiting:
            self.visiting[statement] = True
        elif self.visiting[statement]:
            raise CircularDependencyError
    
    def visit_statement_post(self, statement: Statement):
        self.visiting[statement] = False


@dataclass
class Dependency:
    statement: Statement
    ref_count: int = 1
    no_inline: bool = False
    
    @property
    def can_inline(self):
        if self.no_inline:
            return False
        if self.ref_count > 1:
            return False
        if self.statement.out_options is not None:
            return False
        return True

class DependencyRetriever(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.deps: dict[Statement, Dependency] = {}
    
    def _add_or_increment(self, statement, *args):
        if statement not in self.deps:
            self.deps[statement] = Dependency(statement, *args)
        else:
            self.deps[statement].ref_count += 1
    
    def visit_statement_pre(self, statement: Statement):
        self._add_or_increment(statement)
        if not isinstance(statement, QueryStatement):
            return
        for f in statement.filters:
            for substmt in f.dependencies:
                self._add_or_increment(substmt, 0, True)


class DependencySimplifier(Visitor):
    def __init__(self, deps: dict[Statement, Dependency]) -> None:
        super().__init__()
        self.deps = deps

    def visit_statement_post(self, statement: Statement):
        if not isinstance(statement, QueryStatement):
            return
        
        new_filters: list[Filter] = []
        is_single = lambda stmt: self.deps[stmt].ref_count == 1

        for filt in statement.filters:
            if not isinstance(filt, IntersectsWith):
                new_filters.append(filt)
                continue
            
            substmts = filt.statements
            singles, locked = partition(is_single, substmts)
            for stmt in singles:
                if isinstance(stmt, QueryStatement):
                    new_filters.extend(stmt.filters)
                else:
                    locked.append(stmt)
            if len(locked) > 0:
                new_filters.append(IntersectsWith(*locked))
        
        statement.filters = new_filters


class Compiler(Visitor):
    def __init__(self, root: Statement, deps: dict[Statement, Dependency]) -> None:
        super().__init__()

        self.root = root
        self.deps = deps
        self.variables = VariableManager()
        self.sequence: list[str] = []
    
    def visit_statement_post(self, statement: Statement):
        if statement == self.root:
            self.sequence.append(statement.compile(self.variables))
            self._try_append_out(statement)
        elif not self.deps[statement].can_inline:
            name_to = self.variables.add_statement(statement)
            compiled = statement.compile(self.variables, name_to)
            self.sequence.append(compiled)

            self._try_append_out(statement)
    
    def _try_append_out(self, stmt: Statement):
        if stmt.out_options is None:
            return
        options = stmt.out_options
        var = self.variables.get(stmt)
        out = f".{var} out" if var is not None else "out"
        out += (" " + " ".join(sorted(options))) if len(options) > 0 else ""
        self.sequence.append(out + ";")


def traverse_statement(statement: Statement, visitor: Visitor, visited: set[Statement] | None = None):
    if visited is None:
        visited = set()
    
    statement.accept_pre(visitor)
    if statement in visited:
        return
    visited.add(statement)
    for child in statement.dependencies:
        traverse_statement(child, visitor, visited)
    statement.accept_post(visitor)