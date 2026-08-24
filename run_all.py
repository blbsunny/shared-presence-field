#!/usr/bin/env python3
"""
run_all.py -- the whole sample pipeline, one file.

Reads the five sample clouds in data/, computes the Shared Presence Field over
them at a FIXED sigma = 0.12 m, writes the per-building and merged clouds (with the
scalar field), a per-building table, and four figures, then opens out/.

sigma is FIXED. It is NOT re-selected here. In the paper sigma = 0.12 m was chosen
as the width that maximises the variation of per-building shared presence across
all 68 buildings. Re-running that search on five buildings would land elsewhere and
print a number that contradicts the paper, so it is not run. (Selecting that width
is meaningful only on a full population, so it is not part of this sample pipeline.)
"""
import os
import glob
import csv

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize

from spf.field import shared_presence
from spf.ply_io import read_ply, write_ply_scalar

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")
SIGMA = 0.12                     # FIXED -- see module docstring
BLUE = LinearSegmentedColormap.from_list(
    "spf_blue", ["#04030f", "#10205c", "#1d59b3", "#2f9fe6", "#79e2ff", "#eafdff"])


def iso(pts):
    """Shared isometric view: camera front-right-above. depth large = far."""
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    u = (x + y) / np.sqrt(2.0)
    v = (-x + y + 2.0 * z) / np.sqrt(6.0)
    depth = -x + y - z
    return np.column_stack([u, v]), depth


def scatter_field(ax, pts, S, vmin, vmax):
    """Point cloud in iso view, size + brightness set by shared presence."""
    uv, depth = iso(pts)
    n = np.clip((S - vmin) / (vmax - vmin + 1e-12), 0, 1)
    order = np.argsort(n)                                   # low S first, high S on top
    size = 0.6 + 5.0 * n[order] ** 1.6
    U, V = uv[order, 0], uv[order, 1]
    ax.scatter(U, V, s=size * 4.0, c=S[order], cmap=BLUE, norm=Normalize(vmin, vmax),
               alpha=0.05, linewidths=0, marker=".", rasterized=True)
    ax.scatter(U, V, s=size, c=S[order], cmap=BLUE, norm=Normalize(vmin, vmax),
               alpha=0.9, linewidths=0, marker=".", rasterized=True)
    ax.set_aspect("equal"); ax.axis("off")


def fig_shared_cloud(clouds, fields, path):
    allpts = np.vstack(clouds); allS = np.concatenate(fields)
    vmin, vmax = float(allS.min()), float(allS.max())
    fig = plt.figure(figsize=(7.2, 5.4), facecolor="black")
    ax = fig.add_axes([0.02, 0.02, 0.80, 0.96]); ax.set_facecolor("black")
    scatter_field(ax, allpts, allS, vmin, vmax)
    cax = fig.add_axes([0.85, 0.12, 0.028, 0.7])
    sm = plt.cm.ScalarMappable(Normalize(vmin, vmax), BLUE); sm.set_array([])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("shared presence  S  (sigma = 0.12 m)", color="white", fontsize=9)
    cb.ax.tick_params(colors="white", labelsize=7); cb.outline.set_edgecolor("white")
    fig.savefig(path, facecolor="black", dpi=200); plt.close(fig)


def fig_height_profile(clouds, fields, path):
    BIN = 0.05
    zmax = max(c[:, 2].max() for c in clouds)
    nb = int(np.ceil(zmax / BIN)); edges = np.arange(nb + 1) * BIN
    centers = 0.5 * (edges[:-1] + edges[1:])
    prof = np.full((len(clouds), nb), np.nan)               # per-building median per bin
    for b, (c, S) in enumerate(zip(clouds, fields)):
        z = c[:, 2]; ok = (z >= 0) & (z < edges[-1])
        idx = (z[ok] / BIN).astype(int); s = S[ok]
        o = np.argsort(idx); idx = idx[o]; s = s[o]
        u, st = np.unique(idx, return_index=True)
        for j, k in enumerate(u):
            e = st[j + 1] if j + 1 < len(st) else len(s)
            prof[b, k] = np.median(s[st[j]:e])
    n = np.sum(~np.isnan(prof), 0); v = n > 0
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(prof, 0); p25 = np.nanpercentile(prof, 25, 0); p75 = np.nanpercentile(prof, 75, 0)
    fig = plt.figure(figsize=(4.2, 5.2), facecolor="white")
    ax = fig.add_axes([0.16, 0.10, 0.80, 0.87])
    ax.fill_betweenx(centers[v], p25[v], p75[v], color="black", alpha=0.125, lw=0)
    mm = mean.copy(); mm[~v] = np.nan
    ax.plot(mm, centers, "-", color="#4C4C4C", lw=1.4)
    ax.set_xlabel("shared presence  S  (sigma = 0.12 m)")
    ax.set_ylabel("height above water level, z (m)")
    ax.set_ylim(0, edges[np.max(np.where(v)) + 1]); ax.set_xlim(0, None)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.savefig(path, dpi=200, facecolor="white"); plt.close(fig)


def fig_per_building(letters, medians, path):
    order = np.argsort(medians)[::-1]                        # shared -> singular
    L = [letters[i] for i in order]; M = [medians[i] for i in order]
    fig = plt.figure(figsize=(5.0, 3.2), facecolor="white")
    ax = fig.add_axes([0.10, 0.14, 0.86, 0.80])
    ypos = np.arange(len(L))[::-1]
    ax.barh(ypos, M, color="#4C4C4C", height=0.62)
    for y, m in zip(ypos, M):
        ax.text(m + 0.004, y, f"{m:.3f}", va="center", ha="left", fontsize=9)
    ax.set_yticks(ypos); ax.set_yticklabels(L)
    ax.set_xlim(0, 0.30); ax.set_xlabel("median shared presence  S  (sigma = 0.12 m)")
    ax.set_title("shared  →  singular", fontsize=9, loc="left", color="0.3")
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    fig.savefig(path, dpi=200, facecolor="white"); plt.close(fig)


def fig_kernel_widths(clouds, path):
    sigmas = [0.08, 0.12, 0.20]
    target = clouds[0]                                       # one building
    fields = [shared_presence(target, clouds, s) for s in sigmas]
    vmin = min(f.min() for f in fields); vmax = max(f.max() for f in fields)
    fig = plt.figure(figsize=(9.0, 3.6), facecolor="black")
    for i, (s, S) in enumerate(zip(sigmas, fields)):
        ax = fig.add_axes([0.02 + i * 0.32, 0.06, 0.30, 0.86]); ax.set_facecolor("black")
        scatter_field(ax, target, S, vmin, vmax)
        ax.set_title(f"sigma = {s:.2f} m", color="white", fontsize=10)
    fig.savefig(path, facecolor="black", dpi=200); plt.close(fig)


def open_folder(path):
    try:
        if os.name == "nt":
            os.startfile(path)                              # noqa: S606
        else:
            import subprocess, sys
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
    except Exception:
        pass


def say(msg):
    print(msg, flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(DATA, "*.ply")))
    letters = [os.path.splitext(os.path.basename(f))[0] for f in files]
    say(f"Reading {len(files)} sample clouds from data/ ...")
    clouds = [read_ply(f) for f in files]
    N = len(clouds)

    # per-point field for every building, over ALL buildings (the slow step)
    say(f"Computing shared presence over N = {N} buildings (this is the slow step,")
    say("about a minute -- please wait) ...")
    fields = []
    for i, (L, c) in enumerate(zip(letters, clouds), 1):
        S = shared_presence(c, clouds, SIGMA)
        fields.append(S)
        say(f"  {L}  {float(np.median(S)):.3f}")            # per-building median as each finishes

    # per-building clouds with the scalar + merged shared cloud
    say("Writing point clouds (per-building + merged) to out/ ...")
    for L, c, S in zip(letters, clouds, fields):
        write_ply_scalar(os.path.join(OUT, f"{L}_spf.ply"), c, S)
    write_ply_scalar(os.path.join(OUT, "shared_cloud.ply"),
                     np.vstack(clouds), np.concatenate(fields))

    medians = [float(np.median(S)) for S in fields]
    with open(os.path.join(OUT, "per_building.csv"), "w", newline="") as fp:
        w = csv.writer(fp); w.writerow(["building", "median_shared_presence", "n_points"])
        for L, m, c in zip(letters, medians, clouds):
            w.writerow([L, f"{m:.6f}", len(c)])

    say("Rendering figures (1 shared cloud, 2 height profile, 3 per building, 4 kernel widths) ...")
    fig_shared_cloud(clouds, fields, os.path.join(OUT, "1_shared_cloud.png"))
    fig_height_profile(clouds, fields, os.path.join(OUT, "2_height_profile.png"))
    fig_per_building(letters, medians, os.path.join(OUT, "3_per_building.png"))
    fig_kernel_widths(clouds, os.path.join(OUT, "4_kernel_widths.png"))

    meds = "  ".join(f"{L} {m:.3f}" for L, m in zip(letters, medians))
    print(f"\n{N} buildings, sigma = {SIGMA:.2f} m")
    print(f"per-building median shared presence:  {meds}")
    print("NOTE  these values are computed over N = 5 and are not comparable with the")
    print("      values in the paper, which come from all 68 buildings.")
    print("wrote out/  (4 figures, 6 point clouds, 1 csv)")
    open_folder(OUT)


if __name__ == "__main__":
    main()
