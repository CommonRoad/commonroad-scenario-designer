import numpy as np


def compute_max_curvature_from_polyline(polyline: np.ndarray) -> float:
    """
    Computes the curvature of a given polyline
    :param polyline: The polyline for the curvature computation
    :return: The pseudo maximum curvature of the polyline
    """
    assert isinstance(polyline, np.ndarray) and polyline.ndim == 2 and len(
        polyline[:, 0]) >= 2, 'Polyline malformed for curvature computation p={}'.format(polyline)
    x_d = np.gradient(polyline[:, 0])
    x_dd = np.gradient(x_d)
    y_d = np.gradient(polyline[:, 1])
    y_dd = np.gradient(y_d)

    # compute curvature
    curvature = (x_d * y_dd - x_dd * y_d) / ((x_d ** 2 + y_d ** 2) ** (3. / 2.))

    # compute maximum curvature
    abs_curvature = [abs(ele) for ele in curvature]  # absolute value
    max_curvature = max(abs_curvature)

    # compute pseudo maximum -- mean of the two largest curvatures --> relax the constraint
    abs_curvature.remove(max_curvature)
    second_max_curvature = max(abs_curvature)
    max_curvature = (max_curvature + second_max_curvature) / 2

    return max_curvature