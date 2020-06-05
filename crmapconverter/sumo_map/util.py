from copy import deepcopy
from typing import Dict, List

import numpy as np
from commonroad.geometry.shape import Polygon
from commonroad.scenario.lanelet import LaneletNetwork
from commonroad_cc.collision_detection.pycrcc_collision_dispatch import create_collision_object

# try:
#     import pycrcc
#     from commonroad_cc.collision_detection.pycrcc_collision_dispatch import create_collision_object
#     use_pycrcc = False
# except ModuleNotFoundError:
#     warnings.warn('Commonroad Collision Checker not installed, use shapely instead (slower).')
#     import shapely as shl
#     use_pycrcc = False
use_pycrcc = False


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


def _erode_lanelets(lanelet_network: LaneletNetwork, radius: float=0.4) -> LaneletNetwork:
    """Erode shape of lanelet by given radius."""

    lanelets_ero = []
    crop_meters = 0.3
    min_factor = 0.1
    for lanelet in lanelet_network.lanelets:
        lanelet_ero = deepcopy(lanelet)

        # shorten lanelet by radius
        if len(lanelet_ero._center_vertices) > 4:
            i_max = int((np.floor(len(lanelet_ero._center_vertices) - 1) / 2)) - 1

            i_crop_0 = np.argmax(lanelet_ero.distance >= crop_meters)
            i_crop_1 = len(lanelet_ero.distance) - np.argmax(
                lanelet_ero.distance >= lanelet_ero.distance[-1] - crop_meters)
            i_crop_0 = min(i_crop_0, i_max)
            i_crop_1 = min(i_crop_1, i_max)

            lanelet_ero._left_vertices = lanelet_ero._left_vertices[i_crop_0: -i_crop_1]
            lanelet_ero._center_vertices = lanelet_ero._center_vertices[i_crop_0: -i_crop_1]
            lanelet_ero._right_vertices = lanelet_ero._right_vertices[i_crop_0: -i_crop_1]
        else:
            factor_0 = min(1, crop_meters / lanelet_ero.distance[1])
            lanelet_ero._left_vertices[0] = factor_0 * lanelet_ero._left_vertices[0]\
                                            + (1-factor_0) * lanelet_ero._left_vertices[1]
            lanelet_ero._right_vertices[0] = factor_0 * lanelet_ero._right_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._right_vertices[1]
            lanelet_ero._center_vertices[0] = factor_0 * lanelet_ero._center_vertices[0] \
                                            + (1 - factor_0) * lanelet_ero._center_vertices[1]

            factor_0 = min(1, crop_meters / (lanelet_ero.distance[-1] - lanelet_ero.distance[-2]))
            lanelet_ero._left_vertices[-1] = factor_0 * lanelet_ero._left_vertices[-2] \
                                            + (1 - factor_0) * lanelet_ero._left_vertices[-1]
            lanelet_ero._right_vertices[-1] = factor_0 * lanelet_ero._right_vertices[-2] \
                                             + (1 - factor_0) * lanelet_ero._right_vertices[-1]
            lanelet_ero._center_vertices[-1] = factor_0 * lanelet_ero._center_vertices[-2] \
                                              + (1 - factor_0) * lanelet_ero._center_vertices[-1]

        # compute eroded vector from center
        perp_vecs = (lanelet_ero.left_vertices - lanelet_ero.right_vertices) * 0.5
        length = np.linalg.norm(perp_vecs, axis=1)
        factors = np.divide(radius, length)  # 0.5 * np.ones_like(length))
        factors = np.reshape(factors, newshape=[-1, 1])
        factors = 1 - np.maximum(factors, np.ones_like(factors) * min_factor) # ensure minimum width of eroded lanelet
        perp_vec_ero = np.multiply(perp_vecs, factors)

        # recompute vertices
        lanelet_ero._left_vertices = lanelet_ero.center_vertices + perp_vec_ero
        lanelet_ero._right_vertices = lanelet_ero.center_vertices - perp_vec_ero
        if lanelet_ero._polygon is not None:
            lanelet_ero._polygon = Polygon(np.concatenate((lanelet_ero.right_vertices,
                                                           np.flip(lanelet_ero.left_vertices, 0))))
        lanelets_ero.append(lanelet_ero)

    return LaneletNetwork.create_from_lanelet_list(lanelets_ero)


def _find_intersecting_edges(edges_dict: Dict[int, List[int]], lanelet_network: LaneletNetwork) -> List[List[int]]:
    """

    :param lanelet_network:
    :return:
    """
    eroded_lanelet_network = _erode_lanelets(lanelet_network)
    polygons_dict = {}
    edge_shapes_dict = {}
    for edge_id, lanelet_ids in edges_dict.items():
        edge_shape = []
        for lanelet_id in (lanelet_ids[0], lanelet_ids[-1]):
            if lanelet_id not in polygons_dict:
                polygon = eroded_lanelet_network.find_lanelet_by_id(lanelet_id).convert_to_polygon()

                if use_pycrcc:
                    polygons_dict[lanelet_id] = create_collision_object(polygon)
                else:
                    polygons_dict[lanelet_id] = polygon.shapely_object

                edge_shape.append(polygons_dict[lanelet_id])

        edge_shapes_dict[edge_id] = edge_shape

    intersecting_edges = []
    for edge_id, shape_list in edge_shapes_dict.items():
        for edge_id_other, shape_list_other in edge_shapes_dict.items():
            if edge_id == edge_id_other: continue
            edges_intersect = False
            for shape_0 in shape_list:
                if edges_intersect: break
                for shape_1 in shape_list_other:
                    if use_pycrcc:
                        if shape_0.collide(shape_1):
                            edges_intersect = True
                            intersecting_edges.append([edge_id, edge_id_other])
                            break
                    else:
                        # shapely
                        if shape_0.intersection(shape_1).area > 0.0:
                            edges_intersect = True
                            intersecting_edges.append([edge_id, edge_id_other])
                            break

    return intersecting_edges
