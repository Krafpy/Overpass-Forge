from __future__ import annotations
from .statements import Statement
from .variables import VariableManager
from .base import QueryStatement
from .utils import partition
from .filters import Filter, IntersectsWith


class Visitor:
    def visit_statement_pre(self, statement: Statement):
        pass
    
    def visit_statement_post(self, statement: Statement):
        pass


class CircularDependencyError(Exception):
    pass

class CycleDetectionVisitor(Visitor):
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


class ReferencesCountVisitor(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.refs: dict[Statement, int] = {}
    
    def visit_statement_pre(self, statement: Statement):
        if statement not in self.refs:
            self.refs[statement] = 1
        else:
            self.refs[statement] += 1


class FindFilterDependenciesVisitor(Visitor):
    def __init__(self) -> None:
        super().__init__()
        self.depended_by_filter: set[Statement] = set()
    
    def visit_statement_pre(self, statement: Statement):
        if not isinstance(statement, QueryStatement):
            return
        for f in statement.filters:
            self.depended_by_filter.update(f.dependencies)


class SimplifyDependeciesVisitor(Visitor):
    def __init__(self, refs: dict[Statement, int]) -> None:
        super().__init__()
        self.refs = refs

    def visit_statement_post(self, statement: Statement):
        if not isinstance(statement, QueryStatement):
            return
        
        new_filters: list[Filter] = []
        is_single = lambda stmt: self.refs[stmt] == 1

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


class CompilationVisitor(Visitor):
    def __init__(self, refs: dict[Statement, int], root: Statement, depended_by_filters: set[Statement]) -> None:
        super().__init__()

        self.variables = VariableManager()
        self.root = root
        self.depended_by_filters = depended_by_filters
        self.sequence: list[str] = []
        self.refs = refs
    
    def visit_statement_post(self, statement: Statement):
        to_var = self.refs[statement] > 1 or \
                    statement.out_options is not None or \
                    statement in self.depended_by_filters
        
        if statement == self.root:
            self.sequence.append(statement.compile(self.variables))
            self._try_append_out(statement)
        elif to_var:
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