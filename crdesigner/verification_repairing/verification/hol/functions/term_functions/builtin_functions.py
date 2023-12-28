from typing import Any

import numpy as np


def size(vals: Any) -> int:
    """
    Returns the size.

    :param vals: Values.
    :return: Size.
    """
    return len(vals) if vals is not None else 0


def index(vals: Any, i: int) -> Any:
    """
    Gets the element at index.

    :param vals: Values.
    :param i: Index.
    :return: Element at index.
    """
    return vals[i]


def reverse(vals: Any):
    """
    Reverse the sequence of elements.

    :param vals: Values.
    :return: Reversed values.
    """
    return np.flipud(vals)
