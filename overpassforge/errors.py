from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .base import Statement

class CompilationError(Exception):
    """Raised when an error is detected when building a statement.
    
    Attributes:
        statement: The statement which caused the compile error.
    """

    def __init__(self, msg: str, statement: Optional['Statement'] = None) -> None:
        super().__init__(msg)
        self.statement = statement

class CircularDependencyError(CompilationError):
    """Raised when a statement depending on its own result is detected
    during query build.
    """

    def __init__(self, statement: Optional['Statement'] = None) -> None:
        super().__init__("A statement depends on its own result.", statement)

class UnexpectedCompilationError(CompilationError):
    """Raised when an unexpceted situation occurs during compilation."""
    
    def __init__(self,
        msg: str = "Unexpected compilation error.",
        statement: Optional['Statement'] = None
    ) -> None:
        super().__init__(msg, statement)

class InvalidFilterAttributes(CompilationError):
    """Raised when a filter has invalid attributes."""

    def __init__(self,
        msg: str = "Invalid filter attributes.",
        statement: Optional['Statement'] = None
    ) -> None:
        super().__init__(msg, statement)

class InvalidStatementAttributes(CompilationError):
    """Raised when a statement has invalid attributes."""

    def __init__(self,
        msg: str = "Invalid statement attributes.",
        statement: Optional['Statement'] = None
    ) -> None:
        super().__init__(msg, statement)

class InvalidQuerySettings(CompilationError):
    """Raised on invalid query settings."""

    def __init__(self, msg: str, statement: Optional['Statement'] = None) -> None:
        super().__init__(msg, statement)