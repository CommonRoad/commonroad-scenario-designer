"""
3-D-specific validation helpers – independent of existing 2-D predicates.
"""
from typing import Tuple

import numpy as np
from commonroad.scenario.lanelet import Lanelet

import logging
log3d = logging.getLogger("crdesigner.verification.3d")

def _mean_z(vertices: np.ndarray) -> float:
    """若无 z 轴，则返回 0.0 并在 debug 中提示。"""
    if vertices.shape[1] < 3:
        log3d.debug("2‑D vertices detected -> treat z as 0")
        return 0.0
    return float(np.mean(vertices[:, 2]))

def is_vertical_clearance_sufficient(
    upper: Lanelet,
    lower: Lanelet,
    min_clearance: float = 4.5,
) -> bool:
    """Check that *upper* lanelet rises at least *min_clearance* above *lower*."""
    z_u = _mean_z(upper.center_vertices)
    z_l = _mean_z(lower.center_vertices)
    gap = z_u - z_l
    ok = gap >= min_clearance
    log3d.debug(
        "CLR  gap=%.3f  thr=%.2f  upper=%s  lower=%s  -> %s",
        gap,
        min_clearance,
        upper.lanelet_id,
        lower.lanelet_id,
        ok,
    )
    return ok


def is_grade_within_limit(l: Lanelet, max_grade_pct: float = 8.0) -> bool:
    """Maximum instantaneous slope not larger than *max_grade_pct* (percent)."""
    verts = l.center_vertices
    if verts.shape[1] < 3:
        log3d.debug("GRADE  lanelet=%s is 2‑D → auto‑pass", l.lanelet_id)
        return True

    dz = np.diff(verts[:, 2])
    ds = np.linalg.norm(np.diff(verts[:, :2], axis=0), axis=1)
    grades_pct = np.abs(dz / ds) * 100
    g_max = float(np.max(grades_pct))
    ok = g_max <= max_grade_pct

    log3d.debug(
        "GRADE max=%.2f%%  thr=%.2f%%  lanelet=%s  -> %s",
        g_max,
        max_grade_pct,
        l.lanelet_id,
        ok,
    )
    return ok


def is_vertical_step_reasonable(
    prev: Lanelet,
    succ: Lanelet,
    max_step: float = 0.5,
) -> bool:
    """Avoid cliff-like jumps between connected lanelets."""
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
    """Tunnel must lie below ground but not deeper than *max_depth* (negative)."""
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
