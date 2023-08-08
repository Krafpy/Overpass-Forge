from .base import Statement

class CompilationError(Exception):
    """Raised when an error is detected when building a statement.
    
    Attributes:
        statement: The statement which caused the compile error.
    """

    def __init__(self, msg: str, statement: Statement | None = None) -> None:
        super().__init__(msg)
        self.statement = statement

class CircularDependencyError(CompilationError):
    """Raise when a statement depending on its own result is detected
    during query build.
    
    Attributes:
        statement: The statement that has been deteteced to refer to
            itself.
    """

    def __init__(self, statement: Statement | None = None) -> None:
        super().__init__("A statement depends on its own result.", statement)