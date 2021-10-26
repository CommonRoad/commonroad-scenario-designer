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


def resample_polyline(polyline: np.ndarray, step: float = 2.0) -> np.ndarray:
    """
    Resamples point with equidistant spacing.

    :param polyline: polyline with 2D points
    :param step: sampling interval
    :return: resampled polyline
    """
    if len(polyline) < 2:
        return np.array(polyline)
    new_polyline = [polyline[0]]
    current_position = step
    current_length = np.linalg.norm(polyline[0] - polyline[1])
    current_idx = 0
    while current_idx < len(polyline) - 1:
        if current_position >= current_length:
            current_position = current_position - current_length
            current_idx += 1
            if current_idx > len(polyline) - 2:
                break
            current_length = np.linalg.norm(
                polyline[current_idx + 1] - polyline[current_idx]
            )
        else:
            rel = current_position / current_length
            new_polyline.append(
                (1 - rel) * polyline[current_idx] + rel * polyline[current_idx + 1]
            )
            current_position += step
    new_polyline.append(polyline[-1])
    return np.array(new_polyline)


def compute_curvature_from_polyline(polyline: np.ndarray) -> np.ndarray:
    """
    Computes the curvature of a given polyline

    :param polyline: The polyline for the curvature computation
    :return: The curvature of the polyline
    """
    assert (
        isinstance(polyline, np.ndarray)
        and polyline.ndim == 2
        and len(polyline[:, 0]) >= 2
    ), "Polyline malformed for curvature computation p={}".format(polyline)
    x_d = np.gradient(polyline[:, 0])
    x_dd = np.gradient(x_d)
    y_d = np.gradient(polyline[:, 1])
    y_dd = np.gradient(y_d)

    # compute curvature
    curvature = (x_d * y_dd - x_dd * y_d) / ((x_d ** 2 + y_d ** 2) ** (3.0 / 2.0))
    return curvature


def compute_pathlength_from_polyline(polyline: np.ndarray) -> np.ndarray:
    """
    Computes the path length of a given polyline

    :param polyline: polyline with 2D points
    :return: path length of the polyline
    """
    assert (
        isinstance(polyline, np.ndarray)
        and polyline.ndim == 2
        and len(polyline[:, 0]) >= 2
    ), "Polyline malformed for pathlength computation p={}".format(polyline)
    distance = [0]
    for i in range(1, len(polyline)):
        distance.append(distance[i - 1] + np.linalg.norm(polyline[i] - polyline[i - 1]))
    return np.array(distance)


def compute_orientation_from_polyline(polyline: np.ndarray) -> np.ndarray:
    """
    Computes the orientation of a given polyline

    :param polyline: polyline with 2D points
    :return: orientation of polyline
    """
    assert (
        isinstance(polyline, np.ndarray)
        and len(polyline) > 1
        and polyline.ndim == 2
        and len(polyline[0, :]) == 2
    ), "not a valid polyline. polyline = {}".format(polyline)

    if len(polyline) < 2:
        raise NameError("Cannot create orientation from polyline of length < 2")

    orientation = []
    for i in range(0, len(polyline) - 1):
        pt1 = polyline[i]
        pt2 = polyline[i + 1]
        tmp = pt2 - pt1
        orientation.append(np.arctan2(tmp[1], tmp[0]))

    for i in range(len(polyline) - 1, len(polyline)):
        pt1 = polyline[i - 1]
        pt2 = polyline[i]
        tmp = pt2 - pt1
        orientation.append(np.arctan2(tmp[1], tmp[0]))

    return np.array(orientation)

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
