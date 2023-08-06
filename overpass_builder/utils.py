from typing import Iterable, Callable, TypeVar

T = TypeVar('T')

def partition(pred: Callable[[T], bool], iterable: Iterable[T]) -> tuple[list[T], list[T]]:
    trues, falses = [], []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses