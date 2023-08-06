from __future__ import annotations
from .statements import Statement
from .visitors import traverse_statement, CycleDetector, Compiler, DependencyRetriever, DependencySimplifier
from .base import DATE_FORMAT
from dataclasses import dataclass
from typing import Literal
from datetime import datetime

@dataclass
class Settings:
    """
    Represents an Overpass query's global settings.
    """

    out: Literal["json", "xml", "csv"] = "json"
    timeout: int | None = 25
    maxsize: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    date: datetime | None = None
    diff: tuple[datetime] | tuple[datetime, datetime] | None = None
    csv_fields: tuple[str, ...] | None = None
    csv_header_line: bool = True
    csv_separator: str | None = None

    def compile(self) -> str:
        seq: list[str] = []
        add = lambda s: seq.append(f"[{s}]")
        
        if self.out == "csv":
            if self.csv_fields is None:
                raise AttributeError("Must specify CSV fields when out:csv.")
            frmt = lambda f: "\"{}\"".format(f.strip(' \"\''))
            header = ','.join(map(frmt, self.csv_fields))
            if self.csv_header_line:
                header += f"; true"
            else:
                header += f"; false"
            if self.csv_separator is not None:
                header += f"; {self.csv_separator}"
            add(f"out:csv({header})")
        else:
            add(f"out:{self.out}")
        
        if self.timeout is not None:
            if self.timeout <= 0:
                raise ValueError("Timeout cannot be a negative integer.")
            add(f"timeout:{self.timeout}")
        
        if self.maxsize is not None:
            add(f"maxsize:{self.maxsize}")
        
        if self.bbox is not None:
            add(f"bbox:{','.join(map(str, self.bbox))}")
        
        if self.date is not None:
            add(f"date:\"{self.date.strftime(DATE_FORMAT)}\"")
        
        if self.diff is not None:
            if len(self.diff) == 2:
                a, b = self.diff
                add(f"diff:\"{a.strftime(DATE_FORMAT)}\",\"{b.strftime(DATE_FORMAT)}\"")
            else:
                a, = self.diff
                add(f"diff:\"{a.strftime(DATE_FORMAT)}\"")
        
        return "".join(seq) + ";"



def build(statement: Statement, settings: Settings | None = None):
    """
    Builds the Overpass query string of the given statement, with
    the optional global settings.
    """
    traverse_statement(statement, CycleDetector())
    dependencies = DependencyRetriever()
    traverse_statement(statement, dependencies)
    traverse_statement(statement, DependencySimplifier(dependencies.deps))

    compiler = Compiler(statement, dependencies.deps)
    traverse_statement(statement, compiler)

    core_query = "\n".join(compiler.sequence)
    if settings is not None:
        return f"{settings.compile()}\n{core_query}"
    return core_query