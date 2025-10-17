import numpy as np

def as_xy(p):
    p = np.asarray(p)
    return p[:2] if p.shape[-1] >= 2 else p

def as_xyz(p):
    p = np.asarray(p)
    if p.shape[-1] == 3:
        return p
    if p.shape[-1] == 2:
        return np.array([p[0], p[1], 0.0])
    raise ValueError("Point must have at least 2 dims")

def dist(p1, p2, use_3d: bool):
    if use_3d:
        return np.linalg.norm(as_xyz(p1) - as_xyz(p2))
    else:
        return np.linalg.norm(as_xy(p1) - as_xy(p2))
