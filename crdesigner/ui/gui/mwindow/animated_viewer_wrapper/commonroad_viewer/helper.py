from typing import Tuple
import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch


def _merge_dict(source, destination):
    """deeply merges two dicts
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            _merge_dict(value, node)
        else:
            destination[key] = value
    return destination


def draw_lanelet_polygon(lanelet, ax, color, alpha, zorder,
                         label) -> Tuple[float, float, float, float]:
    # TODO efficiency
    verts = []
    codes = [Path.MOVETO]

    xlim1 = float("Inf")
    xlim2 = -float("Inf")
    ylim1 = float("Inf")
    ylim2 = -float("Inf")

    for x, y in np.vstack([lanelet.left_vertices, lanelet.right_vertices[::-1]]):
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
        ))

    return [xlim1, xlim2, ylim1, ylim2]
