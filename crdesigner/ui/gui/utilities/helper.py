from typing import List

import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path


def _merge_dict(source, destination):
    """deeply merges two dicts"""
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _merge_dict(value, node)
        else:
            destination[key] = value
    return destination


def draw_lanelet_polygon(lanelet, ax, color, alpha, zorder, label) -> List[float]:
    # TODO efficiency
    verts = []
    codes = [Path.MOVETO]

    xlim1 = float("Inf")
    xlim2 = -float("Inf")
    ylim1 = float("Inf")
    ylim2 = -float("Inf")

    for x, y in np.vstack([lanelet.left_vertices[:, :2], lanelet.right_vertices[::-1, :2]]):
        verts.append([x, y])
        codes.append(Path.LINETO)

        xlim1 = min(xlim1, x)
        xlim2 = max(xlim2, x)
        ylim1 = min(ylim1, y)
        ylim2 = max(ylim2, y)

    verts.append(verts[0])
    codes[-1] = Path.CLOSEPOLY

    path = Path(verts, codes)

    ax.add_patch(
        PathPatch(
            path,
            facecolor=color,
            edgecolor="black",
            lw=0.0,
            alpha=alpha,
            zorder=zorder,
            label=label,
        )
    )

    return [xlim1, xlim2, ylim1, ylim2]


def calculate_closest_vertices(point, vertices):
    distances = np.array([])
    for vertex in vertices:
        distance = np.sqrt(np.power(point[0] - vertex[0], 2) + np.power(point[1] - vertex[1], 2))
        distances = np.append(distances, distance)
    shortest_distance_index = np.argmin(distances)
    return shortest_distance_index


def calculate_euclidean_distance(point1, point2):
    distance = np.sqrt(np.power(point1[0] - point2[0], 2) + np.power(point1[1] - point2[1], 2))
    return distance


def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def angle_between(v1, v2):
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    minor = np.linalg.det(np.stack((v2_u[-2:], v1_u[-2:])))
    if minor == 0:
        raise NotImplementedError("Too odd vectors =(")
    return np.sign(minor) * np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
