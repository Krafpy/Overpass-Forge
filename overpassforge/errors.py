from .base import Statement

class CircularDependencyError(Exception):
    """Raise when a statement depending on its own result is detected
    during query build.
    
    Attributes:
        statement: The statement that has been deteteced to refer to
            itself.
    """

    def __init__(self, statement: Statement | None = None) -> None:
        super().__init__(f"A statement depends on its own result.")
        self.statement = statement