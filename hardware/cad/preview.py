#!/usr/bin/env python3
"""Render quick PNG previews of each assembly (matplotlib, no GPU needed)."""
import pathlib, sys
import numpy as np, trimesh
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

ROOT = pathlib.Path(__file__).resolve().parent.parent
def render(device, out, elev=24, azim=-50, hide=("enc_",), zoom=0.62):
    sc = trimesh.load(ROOT / device / f"{device}.glb", force="scene")
    tris, cols = [], []
    for name, g in sc.geometry.items():
        if any(name.startswith(h) for h in hide): continue
        fc = g.visual.face_colors[:, :3] / 255.0
        tris.append(g.triangles); cols.append(fc)
    tris = np.concatenate(tris); cols = np.concatenate(cols)
    # painter's sort by depth
    az, el = np.radians(azim), np.radians(elev)
    view = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    order = np.argsort(tris.mean(1) @ view)
    tris, cols = tris[order], cols[order]
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); n /= (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)
    light = np.clip(np.abs(n @ np.array([0.4, -0.5, 0.8])), 0, 1)[:, None] * 0.55 + 0.45
    fig = plt.figure(figsize=(7, 7), dpi=130); ax = fig.add_axes([0, 0, 1, 1], projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolors=np.clip(cols * light, 0, 1), edgecolors="none"))
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0); c = (lo + hi) / 2; r = (hi - lo).max() / 2 * zoom
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()
    fig.savefig(out, bbox_inches="tight", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    render("cubesat", ROOT / "cubesat" / "cubesat_preview.png", hide=("solar_panel",), zoom=0.55)
    render("rescue_tower", ROOT / "rescue_tower" / "rescue_tower_preview.png", hide=("enc_",), zoom=0.55)
    render("ground_station", ROOT / "ground_station" / "ground_station_preview.png", hide=("enc_lid",), zoom=0.5)
    print("wrote previews")
