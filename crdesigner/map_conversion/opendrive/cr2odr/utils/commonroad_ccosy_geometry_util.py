import numpy as np


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
