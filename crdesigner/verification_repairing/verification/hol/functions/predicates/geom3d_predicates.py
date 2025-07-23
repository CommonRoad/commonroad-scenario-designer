"""
3-D-specific validation helpers – independent of existing 2-D predicates.
"""
from __future__ import annotations

from typing import Iterable, Tuple, List, Set
import numpy as np
from commonroad.scenario.lanelet import Lanelet
import logging

from shapely.geometry import Polygon
from shapely.errors import GEOSException

log3d = logging.getLogger("crdesigner.verification.3d")


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
def is_vertical_clearance_sufficient(upper, lower, min_clearance=4.5, eps_same=0.2):
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


# ---------------------------------------------------------------------------
# (Optional) A version for one-time batch checks, if you want to call a general function in HOL
# ---------------------------------------------------------------------------
# def vertical_clearance_stacked(
#     lanelets: Iterable[Lanelet],
#     min_clearance: float = 4.5,
# ) -> bool:
#     """
#     Perform stacked clearance checks for all lanelets.
#     self-pair / 2D pair are automatically skipped.
#     Returns: True if all satisfy, False otherwise.
#     """
#     checked: Set[Tuple[int, int]] = set()
#     all_ok = True
#     lanelets_list: List[Lanelet] = list(lanelets)

#     for i, upper in enumerate(lanelets_list):
#         for j, lower in enumerate(lanelets_list):
#             if i == j:
#                 continue  # self-pair
#             uid, lid = upper.lanelet_id, lower.lanelet_id
#             if (uid, lid) in checked or (lid, uid) in checked:
#                 continue
#             checked.add((uid, lid))

#             ok = is_vertical_clearance_sufficient(upper, lower, min_clearance)
#             if not ok:
#                 all_ok = False

#     log3d.debug("CLR_STACKED  pairs_checked=%d  result=%s", len(checked), all_ok)
#     return all_ok
