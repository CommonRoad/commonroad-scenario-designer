from __future__ import annotations
import itertools
import logging
import warnings
from collections import Counter
from typing import List, Set


import numpy as np
from shapely import LineString
from shapely.errors import GEOSException
from similaritymeasures import similaritymeasures

from commonroad.scenario.lanelet import Lanelet, StopLine
from commonroad.scenario.traffic_light import TrafficLight
from commonroad.scenario.traffic_sign import TrafficSign
from commonroad_clcs.clcs import CurvilinearCoordinateSystem
from commonroad_clcs.config import CLCSParams, ResamplingParams
from commonroad_clcs.util import (
    chaikins_corner_cutting,
    compute_orientation_from_polyline,
    resample_polyline,
)
from crdesigner.common.config.lanelet2_config import Lanelet2Config

log3d = logging.getLogger("crdesigner.verification.3d")

# ───────────────────── simple attribute helpers ──────────────────────
def lanelet_id(lanelet: Lanelet) -> int:
    return lanelet.lanelet_id


def left_adj(lanelet: Lanelet) -> int:
    return lanelet.adj_left


def right_adj(lanelet: Lanelet) -> int:
    return lanelet.adj_right


def left_polyline(lanelet: Lanelet) -> np.ndarray:
    return lanelet.left_vertices


def right_polyline(lanelet: Lanelet) -> np.ndarray:
    return lanelet.right_vertices


def start_vertex(polyline: np.ndarray) -> np.ndarray:
    return polyline[0]


def end_vertex(polyline: np.ndarray) -> np.ndarray:
    return polyline[-1]


def traffic_signs(lanelet: Lanelet) -> Set[int]:
    return lanelet.traffic_signs


def traffic_lights(lanelet: Lanelet) -> Set[int]:
    return lanelet.traffic_lights


def stop_line(lanelet: Lanelet) -> StopLine:
    return lanelet.stop_line


def predecessors(lanelet: Lanelet) -> List[int]:
    return lanelet.predecessor


def successors(lanelet: Lanelet) -> List[int]:
    return lanelet.successor


def stop_line_traffic_signs(stop_line: StopLine) -> Set[int]:
    return stop_line.traffic_sign_ref


def stop_line_traffic_lights(stop_line: StopLine) -> Set[int]:
    return stop_line.traffic_light_ref


# ────────────────────── reference presence predicates ────────────────
def has_left_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a left adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a left adjacency.
    """
    return lanelet.adj_left is not None


def has_right_adj_ref(lanelet: Lanelet) -> bool:
    """
    Checks whether the lanelet has a reference to a right adjacency.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a reference to a right adjacency.
    """
    return lanelet.adj_right is not None


def has_left_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as left adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as left adjacency.
    """
    return lanelet_0.adj_left == lanelet_1.lanelet_id


def has_right_adj(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether th first lanelet references the second lanelet as right adjacency.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as right adjacency.
    """
    return lanelet_0.adj_right == lanelet_1.lanelet_id


def is_left_adj_same_direction(
    lanelet: Lanelet,
    adj_lanelet: Lanelet,
    *,
    max_z_diff: float = 0.25,
) -> bool:
    """
    Checks whether the left adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the left adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_left_same_direction
        and np.linalg.norm(
            lanelet.left_vertices[0][:2] - adj_lanelet.right_vertices[0][:2]
        )
        < 1
        and np.linalg.norm(
            lanelet.left_vertices[-1][:2] - adj_lanelet.right_vertices[-1][:2]
        )
        < 1
        and _z_close(
            lanelet.left_vertices[0], adj_lanelet.right_vertices[0], max_z_diff
        )
        and _z_close(
            lanelet.left_vertices[-1], adj_lanelet.right_vertices[-1], max_z_diff
        )
    )


def is_left_adj_opposite_direction(
    lanelet: Lanelet,
    adj_lanelet: Lanelet,
    *,
    max_z_diff: float = 0.25,
) -> bool:
    return (
        not lanelet.adj_left_same_direction
        and np.linalg.norm(
            lanelet.left_vertices[0][:2] - adj_lanelet.left_vertices[-1][:2]
        )
        < 1
        and np.linalg.norm(
            lanelet.left_vertices[-1][:2] - adj_lanelet.left_vertices[0][:2]
        )
        < 1
        and _z_close(
            lanelet.left_vertices[0], adj_lanelet.left_vertices[-1], max_z_diff
        )
        and _z_close(
            lanelet.left_vertices[-1], adj_lanelet.left_vertices[0], max_z_diff
        )
    )


def is_right_adj_same_direction(
    lanelet: Lanelet,
    adj_lanelet: Lanelet,
    *,
    max_z_diff: float = 0.25,
) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the same direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        lanelet.adj_right_same_direction
        and np.linalg.norm(
            lanelet.right_vertices[0][:2] - adj_lanelet.left_vertices[0][:2]
        )
        < 1
        and np.linalg.norm(
            lanelet.right_vertices[-1][:2] - adj_lanelet.left_vertices[-1][:2]
        )
        < 1
        and _z_close(
            lanelet.right_vertices[0], adj_lanelet.left_vertices[0], max_z_diff
        )
        and _z_close(
            lanelet.right_vertices[-1], adj_lanelet.left_vertices[-1], max_z_diff
        )
    )


def is_right_adj_opposite_direction(
    lanelet: Lanelet,
    adj_lanelet: Lanelet,
    *,
    max_z_diff: float = 0.25,
) -> bool:
    """
    Checks whether the right adjacency of the lanelet has the opposite direction.

    :param lanelet: Lanelet.
    :param adj_lanelet: Potential adjacent lanelet.
    :return: Boolean indicates whether the right adjacency of the lanelet has the same direction.
    """
    return (
        not lanelet.adj_right_same_direction
        and np.linalg.norm(
            lanelet.right_vertices[0][:2] - adj_lanelet.right_vertices[-1][:2]
        )
        < 1
        and np.linalg.norm(
            lanelet.right_vertices[-1][:2] - adj_lanelet.right_vertices[0][:2]
        )
        < 1
        and _z_close(
            lanelet.right_vertices[0], adj_lanelet.right_vertices[-1], max_z_diff
        )
        and _z_close(
            lanelet.right_vertices[-1], adj_lanelet.right_vertices[0], max_z_diff
        )
    )


def _z_close(v0: np.ndarray, v1: np.ndarray, max_diff: float) -> bool:
    """Return *True* if |z₀−z₁| ≤ max_diff or vertices are 2-D."""
    if v0.shape[0] < 3 or v1.shape[0] < 3:
        return True
    return abs(v0[2] - v1[2]) <= max_diff


def is_correct_left_right_boundary_assignment(lanelet: Lanelet) -> bool:
    """
    Checks whether the boundaries of two polylines are swapped.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the two boundaries should be swapped.
    """
    return not _wrong_left_right_boundary_side(
        lanelet.center_vertices, lanelet.left_vertices, lanelet.right_vertices
    )


def _wrong_left_right_boundary_side(
    center_vertices: np.ndarray,
    left_vertices: np.ndarray,
    right_vertices: np.ndarray,
    config: Lanelet2Config = Lanelet2Config(),
    *,
    max_z_diff: float = 0.25,
) -> bool:
    """
    Checks whether left and right boundary are swapped.

    :param center_vertices: Center vertices of lanelet.
    :param left_vertices: Left boundary of lanelet.
    :param right_vertices: Right boundary of lanelet.
    :returns: Boolean indicating whether boundaries are swapped.
    """
    left, right = None, None
    center_vertices = chaikins_corner_cutting(center_vertices, config.chaikins_initial_refinements)
    center_vertices = resample_polyline(center_vertices, config.resampling_initial_step)
    for eps, max_polyline_resampling_step in itertools.product(
        config.eps2_values, config.max_polyline_resampling_step_values
    ):
        try:
            if len(center_vertices) == 2:
                center_vertices = np.insert(
                    center_vertices, 1, (center_vertices[0] + center_vertices[1]) / 2, axis=0
                )
            cpar = CLCSParams(
                eps2=eps,
                resampling=ResamplingParams(
                    fixed_step=max_polyline_resampling_step, interpolation_type="linear"
                ),
            )
            ccs = CurvilinearCoordinateSystem(center_vertices, cpar, False)
            left = np.array(
                [ccs.convert_to_curvilinear_coords(v[0], v[1])[1] for v in left_vertices]
            )
            right = np.array(
                [ccs.convert_to_curvilinear_coords(v[0], v[1])[1] for v in right_vertices]
            )
            break
        except Exception:
            center_vertices = chaikins_corner_cutting(
                center_vertices, config.chaikins_repeated_refinements
            )
            center_vertices = resample_polyline(center_vertices, config.resampling_repeated_step)
            continue

    # ---- fallback handling ----
    if left is None or right is None:
        warnings.warn(
            "Could not project lanelet boundaries to the curvilinear "
            "coordinate system – treating assignment as WRONG."
        )
        return True  # indicates "possible swap" detected, hand over to upper layer for processing

    # Original decision logic
    return (sum(left - right >= 0) / len(left)) < config.perc_vert_wrong_side


def has_predecessor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as predecessor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as predecessor.
    """
    return lanelet_1.lanelet_id in lanelet_0.predecessor


def has_successor(lanelet_0: Lanelet, lanelet_1: Lanelet) -> bool:
    """
    Checks whether the first lanelet references the second lanelet as successor.

    :param lanelet_0: First lanelet.
    :param lanelet_1: Second lanelet.
    :return: Boolean indicates whether the first lanelet references the second lanelet as successor.
    """
    return lanelet_1.lanelet_id in lanelet_0.successor


def has_traffic_sign(lanelet: Lanelet, traffic_sign: TrafficSign) -> bool:
    """
    Checks whether the lanelet references the traffic sign.

    :param lanelet: Lanelet.
    :param traffic_sign: Traffic sign.
    :return: Boolean indicates whether the lanelet references the traffic sign.
    """
    return traffic_sign.traffic_sign_id in lanelet.traffic_signs


def has_traffic_light(lanelet: Lanelet, traffic_light: TrafficLight) -> bool:
    """
    Checks whether the lanelet references the traffic light.

    :param lanelet: Lanelet.
    :param traffic_light: Traffic light.
    :return: Boolean indicates whether the lanelet references the traffic light.
    """
    return traffic_light.traffic_light_id in lanelet.traffic_lights


def is_polylines_intersection(
    polyline_0: np.ndarray,
    polyline_1: np.ndarray,

    min_clearance: float = 0.25,
) -> bool:
    """
    Checks whether two polylines intersect each other.

    :param polyline_0: First polyline.
    :param polyline_1: Second lanelet.
    :return: Boolean indicates whether two polylines intersect each other.
    """
    line_0 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_0]
    line_1 = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline_1]
    result = LineString(line_0).intersection(LineString(line_1))

    if result.is_empty:
        return False

    # if clearance requested & data is 3-D, measure Δz at closest vertices
    if (
        min_clearance > 0
        and polyline_0.shape[1] == 3
        and polyline_1.shape[1] == 3
    ):
        inter_xy = np.array(result.coords[0][:2])
        z0 = polyline_0[
            np.argmin(np.linalg.norm(polyline_0[:, :2] - inter_xy, axis=1))
        ][2]
        z1 = polyline_1[
            np.argmin(np.linalg.norm(polyline_1[:, :2] - inter_xy, axis=1))
        ][2]
        if abs(z0 - z1) >= min_clearance:
            return False
    return True


def is_polyline_self_intersection(
    polyline: np.ndarray,

    min_clearance: float = 0.25,
) -> bool:
    line = [(x, y, z[0]) if z else (x, y) for x, y, *z in polyline]
    orientation = compute_orientation_from_polyline(
        polyline[:, :2]
    )  # function does not support 3d vertices
    orientation_dif = [
        abs(orientation[i + 1] - orientation[i]) for i in range(len(orientation) - 1)
    ]
    line_string = LineString(line)

    base_cond = (
        (not line_string.is_simple)
        or Counter(line).most_common(1)[0][1] > 1
        or np.isclose(np.max(orientation_dif), np.pi)
    )
    if not base_cond:
        return False

    if min_clearance > 0 and polyline.shape[1] == 3:
        z_vals = polyline[:, 2]
        if (z_vals.max() - z_vals.min()) >= min_clearance:
            return False
    return True


def are_equal_vertices(
    vertex_0: np.ndarray,
    vertex_1: np.ndarray,
    *,
    tol_xy: float = 1e-5,
    tol_z: float = 0.01,
) -> bool:
    xy_close = np.linalg.norm(vertex_0[:2] - vertex_1[:2]) < tol_xy
    if vertex_0.shape[0] < 3 or vertex_1.shape[0] < 3:
        return xy_close
    return xy_close and abs(vertex_0[2] - vertex_1[2]) < tol_z

from shapely.validation import make_valid     # shapely>=2
from shapely.errors import GEOSException
def _clean_poly(poly):
    if not poly.is_valid:
        try:
            return make_valid(poly)           # try to fix
        except Exception:
            return poly.buffer(0)             # classic fallback
    return poly
def are_intersected_lanelets(
    lanelet_0: Lanelet,
    lanelet_1: Lanelet,

    min_clearance: float = 0.0,
) -> bool:
    """
    Returns **True** if the lanelets *do not* geometrically clash in
    an invalid way (legacy semantics preserved).
    """
    p0 = _clean_poly(lanelet_0.polygon.shapely_object)
    p1 = _clean_poly(lanelet_1.polygon.shapely_object)

    try:
        result = p0.intersection(p1, grid_size=0.05)  # given grid size can reduce precision issues
    except GEOSException as e:
        logging.warning(
            "GEOSException between lanelet %s and %s: %s – treating as 'intersected' so that validator flags it.",
            lanelet_0.lanelet_id, lanelet_1.lanelet_id, e)
        return True      # let validator think "intersected" so that it flags it for later repair
    
    if (
        min_clearance > 0
        and lanelet_0.center_vertices.shape[1] == 3
        and lanelet_1.center_vertices.shape[1] == 3
    ):
        z0 = np.mean(lanelet_0.center_vertices[:, 2])
        z1 = np.mean(lanelet_1.center_vertices[:, 2])
        if abs(z0 - z1) >= min_clearance:
            return True          # vertical clearance is sufficient, consider as "not intersected"

    return not result.is_empty


def has_stop_line(lanelet: Lanelet):
    """
    Checks whether the lanelet has a stop line.

    :param lanelet: Lanelet.
    :return: Boolean indicates whether the lanelet has a stop line
    """
    return lanelet.stop_line is not None


def has_start_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has a start point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has a start point.
    """
    return stop_line.start is not None


def has_end_point(stop_line: StopLine) -> bool:
    """
    Checks whether the stop line has an end point.

    :param stop_line: Stop line.
    :return: Boolean indicates whether the stop line has an end point.
    """
    return stop_line.end is not None


def are_similar_polylines(polyline_0: np.ndarray, polyline_1: np.ndarray) -> bool:
    """
    Checks the similarity of two polylines.

    :param polyline_0: First polyline symbol.
    :param polyline_1: Second polyline symbol.
    :return: Boolean symbol indicates whether the two polylines are similar.
    """
    # initial or final vertices are not similar
    if not (
        (np.linalg.norm(polyline_0[0] - polyline_1[0]) < 1)
        and (np.linalg.norm((polyline_0[-1] - polyline_1[-1]) < 1))
        or (
            (np.linalg.norm(polyline_0[0] - polyline_1[-1]) < 1)
            and (np.linalg.norm(polyline_0[-1] - polyline_1[0]) < 1)
        )
    ):
        return False
    # length is completely different
    if (
        Lanelet._compute_polyline_cumsum_dist([polyline_0])[-1]
        - Lanelet._compute_polyline_cumsum_dist([polyline_1])[-1]
        > 50
    ):
        return False
    # all vertices are quite close
    if polyline_0.shape[0] == polyline_1.shape[0] and all(
        [dist < 0.01 for dist in np.linalg.norm(polyline_0 - polyline_1, axis=1)]
    ):
        return True
    return similaritymeasures.frechet_dist(polyline_0, polyline_1) < 1e-6
    # TODO: Use thresh of config and update parameter above in this function


def is_adj_type(
    lanelet: Lanelet,
    adj: Lanelet,
    exp_adj_type: str,
    *,
    max_z_diff: float = 0.25,
) -> bool:
    """
    Identifies the type of adjacency of lanelet. The types include parallel, merging, and forking adjacencies.

    :param lanelet: Lanelet.
    :param adj: Adjacency.
    :param exp_adj_type: Expected adjacent type.
    :return: Boolean indicates whether the expected adjacent type is equal to the computed type.
    """
    parallel, merging, forking = "parallel", "merging", "forking"

    is_left = lanelet.adj_left == adj.lanelet_id
    is_same_dir = (
        lanelet.adj_left_same_direction
        if is_left
        else lanelet.adj_right_same_direction
    )

    # stacked in z → automatically parallel
    if not _z_close(
        lanelet.center_vertices[0], adj.center_vertices[0], max_z_diff
    ):
        return exp_adj_type == parallel

    if not is_same_dir:
        return exp_adj_type == parallel

    # analyse xy-shape distances
    if is_left:
        adj_poly = adj.right_vertices
    else:
        adj_poly = adj.left_vertices

    left_poly = lanelet.left_vertices
    right_poly = lanelet.right_vertices

    adj_size = len(adj_poly)
    lan_size = len(left_poly)

    left_start_dist = np.linalg.norm(left_poly[0] - adj_poly[0])
    left_end_dist = np.linalg.norm(left_poly[lan_size - 1] - adj_poly[adj_size - 1])

    right_start_dist = np.linalg.norm(right_poly[0] - adj_poly[0])
    right_end_dist = np.linalg.norm(right_poly[lan_size - 1] - adj_poly[adj_size - 1])

    if left_start_dist > right_start_dist and left_end_dist < right_end_dist:
        adj_type = forking if is_left else merging
    elif left_start_dist < right_start_dist and left_end_dist > right_end_dist:
        adj_type = merging if is_left else forking
    else:
        adj_type = parallel

    return adj_type == exp_adj_type


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _mean_z(vertices: np.ndarray) -> float:
    """if there are no z-coordinates, return 0.0"""
    if vertices.shape[1] < 3:
        log3d.debug("2‑D vertices detected -> treat z as 0")
        return 0.0
    return float(np.mean(vertices[:, 2]))

def _xy_overlap(l1, l2, area_tol=1e-3, length_tol=1e-3):
    """Check if two lanelets have substantial overlap in the XY plane (greater than tol area)"""
    try:
        g1 = l1.polygon.shapely_object
        g2 = l2.polygon.shapely_object
        inter = g1.intersection(g2)
        if inter.is_empty:
            return False
        if hasattr(inter, "area") and inter.area > area_tol:
            return True
        if hasattr(inter, "length") and inter.length > length_tol:
            return True
        return False
    except GEOSException as e:
        log3d.debug("XY overlap failed (%s,%s): %s", l1.lanelet_id, l2.lanelet_id, e)
        return False


# ---------------------------------------------------------------------------
# Atomic predicates 
# used in HOL formulas, e.g. `Is_vertical_clearance_sufficient(l1, l2, 4.5)`.
# ---------------------------------------------------------------------------
def is_vertical_clearance_sufficient(upper, lower, min_clearance=4.5, eps_same=0.2)-> bool:
    # 1) if no XY overlap, skip
    if not _xy_overlap(upper, lower):
        log3d.debug("CLR  skip (no XY overlap) upper=%s lower=%s", upper.lanelet_id, lower.lanelet_id)
        return True
    # 2) self pair
    if upper.lanelet_id == lower.lanelet_id:
        return True
    # 3) if either is 2D, skip
    if upper.center_vertices.shape[1] < 3 or lower.center_vertices.shape[1] < 3:
        return True

    zu = _mean_z(upper.center_vertices)
    zl = _mean_z(lower.center_vertices)
    gap = abs(zu - zl)

    # 4) if basically the same layer (gap is small), consider it as no need for clearance check
    if gap < eps_same:
        log3d.debug("CLR  same layer (gap=%.3f<%.3f) upper=%s lower=%s -> pass",
                    gap, eps_same, upper.lanelet_id, lower.lanelet_id)
        return True

    ok = gap >= min_clearance
    log3d.debug("CLR  gap=%.3f thr=%.2f upper=%s lower=%s -> %s",
                gap, min_clearance, upper.lanelet_id, lower.lanelet_id, ok)
    return ok


def is_grade_within_limit(l: Lanelet, max_grade_pct: float = 8.0) -> bool:
    verts = l.center_vertices
    if verts.shape[1] < 3:
        log3d.debug("GRADE lanelet=%s is 2D → pass", l.lanelet_id)
        return True

    dz = np.diff(verts[:, 2])
    ds = np.linalg.norm(np.diff(verts[:, :2], axis=0), axis=1)

    mask = ds < 0.01   # adjust according to coordinate scale
    dz, ds = dz[~mask], ds[~mask]
    if dz.size == 0:
        log3d.debug("GRADE lanelet=%s no effective seg → pass", l.lanelet_id)
        return True

    grades_pct = np.abs(dz / ds) * 100
    g_max = float(np.max(grades_pct))
    ok = g_max <= max_grade_pct

    if not ok:
        idx = int(np.argmax(grades_pct))
        log3d.debug(
            "GRADE fail seg=%d dz=%.3f ds=%.3f grade=%.2f%% thr=%.2f lanelet=%s",
            idx, dz[idx], ds[idx], grades_pct[idx], max_grade_pct, l.lanelet_id
        )
        # Further print the original coordinates
        p0 = verts[idx]
        p1 = verts[idx+1]
        log3d.debug("    seg pts: p0=(%.3f, %.3f, %.3f) p1=(%.3f, %.3f, %.3f)",
                    p0[0], p0[1], p0[2] if verts.shape[1]>2 else 0,
                    p1[0], p1[1], p1[2] if verts.shape[1]>2 else 0)
    return ok


def is_vertical_step_reasonable(
    prev: Lanelet,
    succ: Lanelet,
    max_step: float = 0.5,
) -> bool:
    """Check if the height change between adjacent (predecessor→successor) lanelets does not exceed max_step."""
    zp = _mean_z(prev.center_vertices[-1:])
    zs = _mean_z(succ.center_vertices[:1])
    diff = abs(zp - zs)
    ok = diff <= max_step
    log3d.debug(
        "STEP  diff=%.3f  thr=%.2f  prev=%s  succ=%s  -> %s",
        diff,
        max_step,
        prev.lanelet_id,
        succ.lanelet_id,
        ok,
    )
    return ok


def is_tunnel_depth_valid(
    l: Lanelet,
    ground_z: float = 0.0,
    max_depth: float = 5.0,
) -> bool:
    """Check if the tunnel is below ground (z<ground_z) but not deeper than max_depth."""
    z_mean = _mean_z(l.center_vertices)
    depth = ground_z - z_mean
    ok = 0.0 <= depth <= max_depth
    log3d.debug(
        "TUNNEL depth=%.3f  max=%.2f  lanelet=%s  -> %s",
        depth,
        max_depth,
        l.lanelet_id,
        ok,
    )
    return ok