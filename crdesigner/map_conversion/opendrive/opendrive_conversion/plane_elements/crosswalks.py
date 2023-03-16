import numpy as np
from typing import List
from crdesigner.map_conversion.common.conversion_lanelet import  ConversionLanelet


def get_crosswalks(road) -> List[ConversionLanelet]:
    """ identify and convert crosswalks

    :param road: The road object from which to extract signals.
    :type road: :class:`Road`
    :return: list of ConversionLanelets with lanelet_type='crosswalk'
    :rtype: list[ConversionLanelet]
    """
    crosswalks = []
    for crosswalk in [obj for obj in road.objects if obj.type == "crosswalk"]:
        pos, tan, _, _ = road.planView.calc(crosswalk.s, compute_curvature=False)
        position = np.array(
                [pos[0] + crosswalk.t * np.cos(tan + np.pi / 2), pos[1] + crosswalk.t * np.sin(tan + np.pi / 2)])
        corners = np.empty((0, 2))
        # origin of local u/v coordinate system that hdg rotates about
        o = np.atleast_2d(position)
        # rotation matrix
        rotation_angle = tan + crosswalk.hdg
        rotation_matrix = np.array([[np.cos(rotation_angle), -np.sin(rotation_angle)],
                                    [np.sin(rotation_angle), np.cos(rotation_angle)]])

        for outline in crosswalk.outline:
            p = np.atleast_2d([position[0] + outline.u, position[1] + outline.v])
            # rotate every point
            rot_p = np.squeeze((rotation_matrix @ (p.T - o.T) + o.T).T)
            corners = np.vstack((corners, rot_p))

        # indices 1 and 2 of corners define the left bound
        left_vertices = np.array([corners[1], corners[2]])
        # indices 0 and 3 of corners define the right bound
        right_vertices = np.array([corners[0], corners[3]])

        center_vertices = (left_vertices + right_vertices) / 2
        # create ConversionLanelet
        lanelet = ConversionLanelet(None, left_vertices, center_vertices, right_vertices, crosswalk.id,
                                    lanelet_type='crosswalk')
        crosswalks.append(lanelet)
    return crosswalks
