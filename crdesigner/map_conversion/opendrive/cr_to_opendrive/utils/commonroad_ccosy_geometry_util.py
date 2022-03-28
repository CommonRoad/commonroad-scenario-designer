import numpy as np


def chaikins_corner_cutting(polyline: np.ndarray, refinements: int = 1) -> np.ndarray:
    """
    Chaikin's corner cutting algorithm to smooth a polyline by replacing each original point with two new points.
    The new points are at 1/4 and 3/4 along the way of an edge.

    :param polyline: polyline with 2D points
    :param refinements: how many times apply the chaikins corner cutting algorithm
    :return: smoothed polyline
    """
    for _ in range(refinements):
        L = polyline.repeat(2, axis=0)
        R = np.empty_like(L)
        R[0] = L[0]
        R[2::2] = L[1:-1:2]
        R[1:-1:2] = L[2::2]
        R[-1] = L[-1]
        polyline = L * 0.75 + R * 0.25

    return polyline


def remove_duplicates_from_polyline(polyline: np.ndarray) -> np.ndarray:
    """

    :param polyline: polyline with 2D points
    :return: path length of the polyline
    """
    assert (
        isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(polyline) > 0
    ), "Polyline malformed for pathlength computation p={}".format(polyline)
    new_polyline = [(polyline[0])]

    old_value = polyline[0]
    for i in range(1, len(polyline - 1)):
        value = polyline[i]
        if old_value[0] != value[0] or old_value[1] != value[1]:
            new_polyline.append(value)
        old_value = value

    return np.array(new_polyline)
