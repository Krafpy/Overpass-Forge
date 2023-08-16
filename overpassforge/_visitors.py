from __future__ import annotations
from .base import Statement
from .statements import RawStatement
from ._variables import VariableManager
from .base import Set
from ._utils import partition
from .filters import Filter, Intersection
from .errors import CircularDependencyError
from dataclasses import dataclass


class Visitor:
    """
    Base visitor class.
    """
    def visit_statement_pre(self, statement: Statement):
        pass
    
    def visit_statement_post(self, statement: Statement):
        pass


class CycleDetector(Visitor):
    """
    A visitor to detected cycles in a statement's dependency,
    raises a `CircularDependencyError` exception if detected.
    """
    def __init__(self) -> None:
        super().__init__()
        self.visiting: dict[Statement, bool] = {}
    
    def visit_statement_pre(self, statement: Statement):
        if statement not in self.visiting:
            self.visiting[statement] = True
        elif self.visiting[statement]:
            raise CircularDependencyError(statement)
    
    def visit_statement_post(self, statement: Statement):
        self.visiting[statement] = False


@dataclass
class Dependency:
    """
    Stores additional information on a specific dependency.
    """
    statement: Statement
    ref_count: int = 1
    no_inline: bool = False
    
    @property
    def can_inline(self):
        return not self.no_inline and self.ref_count <= 1 and len(self.statement.out_options) == 0

class DependencyRetriever(Visitor):
    """
    Collects information on the dependencies in a statement's graph.
    """
    def __init__(self) -> None:
        super().__init__()
        self.deps: dict[Statement, Dependency] = {}
    
    def visit_statement_pre(self, statement: Statement):
        if statement not in self.deps:
            self.deps[statement] = Dependency(statement)
        else:
            self.deps[statement].ref_count += 1

        # If we are compiling raw statement, all of its
        # dependencies must be stored in variables
        if statement.__class__ is RawStatement:
            for stmt in statement._dependencies:
                if stmt not in self.deps:
                    self.deps[stmt] = Dependency(stmt, 0, True)
            return
        # Dependencies used by filters must always from variables
        if isinstance(statement, Set):
            for f in statement.filters:
                for stmt in f._dependencies:
                    if stmt not in self.deps:
                        self.deps[stmt] = Dependency(stmt, 0, True)


class DependencySimplifier(Visitor):
    """
    Simplifies chained filter dependencies. For example:
    ```text
        node[tourism=yes]->set_0;
        node.set_0[amenity=restaurant];
    ```
    becomes:
    ```text
        node[tourism=yes][amenity=restaurant];
    ```
    """
    def __init__(self, deps: dict[Statement, Dependency]) -> None:
        super().__init__()
        self.deps = deps

    def visit_statement_post(self, statement: Statement):
        if not isinstance(statement, Set):
            return statement
        
        new_filters: list[Filter] = []
        is_single = lambda stmt: self.deps[stmt].ref_count == 1

        for filt in statement.filters:
            if not isinstance(filt, Intersection):
                new_filters.append(filt)
                continue
            
            substmts = filt.statements
            singles, locked = partition(is_single, substmts)
            for stmt in singles:
                if isinstance(stmt, Set) and \
                    stmt.__class__ is statement.__class__:
                    new_filters.extend(stmt.filters)
                else:
                    locked.append(stmt)
            if len(locked) > 0:
                new_filters.append(Intersection(*locked))
        
        statement.filters = new_filters
        return statement


class Compiler(Visitor):
    """
    Compiles a statement: builds a sequence of string that once
    concatenated represents the compiled statement's query string.
    """
    def __init__(self, root: Statement, deps: dict[Statement, Dependency]) -> None:
        super().__init__()

        self.root = root
        self.deps = deps
        self.variables = VariableManager()
        self.sequence: list[str] = []
    
    def visit_statement_post(self, statement: Statement):
        # Other statement that can be inlined are automatically
        # handled in each statement's compilation

        if statement == self.root:
            self.sequence.append(statement._compile(self.variables))
        elif not self.deps[statement].can_inline:
            name_to = self.variables.add_statement(statement)
            compiled = statement._compile(self.variables, name_to)
            self.sequence.append(compiled)


def traverse_statement(statement: Statement, visitor: Visitor):
    """
    Applies on a visitor on the statement's dependency graph in a
    Depth-First Search manner. The graph must not contain cycles.
    If a substatement is referenced more that once it will be pre-visited
    multiple times but post-visited only once.
    """

    visited = set[Statement]()

    def traverse(statement: Statement):
        statement._accept_pre(visitor)
        if statement in visited:
            return statement
        visited.add(statement)
        for dep in statement._dependencies:
            traverse(dep)
        statement._accept_post(visitor)
    
    traverse(statement)

    # def traverse(stmt: Statement):
    #     return traverse_statement(stmt, visitor, visited)

    # match statement:
    #     case Elements(filters=filters):
    #         new_filters = []
    #         for filt in filters:
    #             match filt:
    #                 case Intersection(statements=others):
    #                     new_filters.append(Intersection(*map(traverse, others)))
    #                 case Area(input_area=areas):
    #                     new_areas = cast(Areas, traverse(areas))
    #                     new_filters.append(Area(input_area=new_areas))
    #                 case Pivot(input_area=areas):
    #                     new_areas = cast(Areas, traverse(areas))
    #                     new_filters.append(Pivot(input_area=new_areas))
    #                 case Around(radius=r, input_set=input_set, lats=lats, lons=lons):
    #                     new_set = None
    #                     if input_set is not None:
    #                         new_set = traverse(input_set)
    #                     new_filters.append(Around(r, new_set, lats, lons))
    #                 case _:
    #                     new_filters.append(filt)
            
    #         statement.filters = new_filters
        
    #     case Union(sets=sets):
    #         statement.sets = cast(list[Set], list(map(traverse, sets)))
        
    #     case Difference(a=a, b=b):
    #         statement.a = cast(Set, traverse(a))
    #         statement.b = cast(Set, traverse(b))
        
    #     case RawStatement(_dependency_dict=deps):
    #         statement._dependency_dict = {name: traverse(stmt) for name, stmt in deps.items()}

    # return visitor.visit_statement_post(statement)