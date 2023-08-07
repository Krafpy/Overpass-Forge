from typing import Iterable, Callable, TypeVar
import re


T = TypeVar('T')

def partition(pred: Callable[[T], bool], iterable: Iterable[T]) -> tuple[list[T], list[T]]:
    trues, falses = [], []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


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