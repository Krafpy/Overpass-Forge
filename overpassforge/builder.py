from __future__ import annotations
from .statements import Statement
from ._visitors import traverse_statement as _traverse
from ._visitors import CycleDetector as _CycleDetector
from ._visitors import Compiler as _Compiler
from ._visitors import DependencyRetriever as _DependencyRetriever
from ._visitors import DependencySimplifier as _DependencySimplifier
from .base import DATE_FORMAT
from dataclasses import dataclass
from typing import Literal
from datetime import datetime
import copy
import re

@dataclass
class Settings:
    """Global settings of an Overpass query.
    See the `Overpass reference <https://wiki.openstreetmap.org/wiki/Overpass_API/Overpass_QL#Settings>`_
    for more details.
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

    def _compile(self) -> str:
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



def build(statement: Statement, settings: Settings | None = None) -> str:
    """Builds the Overpass query string of the given statement, with
    the optional global settings.

    Args:
        statement: The statement to compile.
        settings: Global query settings to append at the top of the generated query.
    
    Returns:
        The compiled Overpass query.

    Raises:
        CircularDependencyError: One of the substatements requires its own result.
        AttributeError: Invalid (sub)statement.
        RuntimeError: Unexpected internal compilation error.
    """
    statement = copy.deepcopy(statement)
    _traverse(statement, _CycleDetector())
    dependencies = _DependencyRetriever()
    _traverse(statement, dependencies)
    _traverse(statement, _DependencySimplifier(dependencies.deps))

    compiler = _Compiler(statement, dependencies.deps)
    _traverse(statement, compiler)

    core_query = "\n".join(compiler.sequence)
    if settings is not None:
        return f"{settings._compile()}\n{core_query}"
    return core_query

def beautify(query: str) -> str:
    """
    Beautifies a compiled query string (i.e. adds indentation, line breaks...)
    """
    query, _ = re.subn(r"\(\(", "(\n(\n", query)
    query, _ = re.subn(r"(\n\(|^\()", "\n(\n", query)
    query, _ = re.subn(r"\n\n", "\n", query)
    query, _ = re.subn(r"\)\;", "\n);", query)
    query, _ = re.subn(r"\)\-\>", "\n)->", query)
    query, _ = re.subn(r"\; ", ";\n", query)

    indented = ""
    indent = 0
    i = 0
    while i < len(query):
        next_one = query[i]
        next_two = query[i:min(i+2,len(query))]
        if next_two == "(\n":
            indent += 1
            indented += "(\n" + "  " * indent
            i += 2
        elif next_two == "\n)":
            indent -= 1
            indented += "\n" + "  " * indent + ")"
            i += 2
        elif next_one == "\n":
            indented += "\n" + "  " * indent
            i += 1
        else:
            indented += query[i]
            i += 1
    
    return indented