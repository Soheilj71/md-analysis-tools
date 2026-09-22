#!/usr/bin/env python3
# fes_2d_from_points.py
# Goal:
#   - Load 2D points from .npy (shape (N,2) or (n_traj,n_steps,2))
#   - Build a 2D histogram probability P(x,y)
#   - Convert to free energy: F(x,y) = -kT * ln(P)
#   - Shift so minimum free energy is 0 (common in papers)
#   - Save the grid (npz) and a plot (png)

import argparse
import sys
from pathlib import Path
import numpy as np

# Matplotlib is used only for plotting.
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def fail(message: str, code: int = 1) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(code)


def load_points(path: Path) -> np.ndarray:
    if not path.exists():
        fail(f"Input file not found: {path}")

    arr = np.load(str(path))
    arr = np.asarray(arr, dtype=float)

    # Accept (N,2) directly.
    if arr.ndim == 2 and arr.shape[1] == 2:
        pts = arr

    # Accept (n_traj, n_steps, 2) and flatten into (N,2).
    elif arr.ndim == 3 and arr.shape[-1] == 2:
        pts = arr.reshape(-1, 2)

    else:
        fail(f"Expected shape (N,2) or (n_traj,n_steps,2). Got: {arr.shape}")

    # Remove bad numeric rows (NaN/inf).
    good = np.isfinite(pts).all(axis=1)
    pts = pts[good]

    if pts.shape[0] < 50:
        fail(f"Too few valid points after cleaning ({pts.shape[0]}). Need more for a stable FES.")

    return pts


def pick_range(points: np.ndarray, xlim, ylim, pad_frac: float = 0.05):
    # If user provided xlim/ylim, use them.
    if xlim is not None and ylim is not None:
        return (xlim[0], xlim[1], ylim[0], ylim[1])

    # Otherwise choose range from data, with a small padding.
    xmin = float(points[:, 0].min())
    xmax = float(points[:, 0].max())
    ymin = float(points[:, 1].min())
    ymax = float(points[:, 1].max())

    xpad = (xmax - xmin) * pad_frac if xmax > xmin else 1.0
    ypad = (ymax - ymin) * pad_frac if ymax > ymin else 1.0

    return (xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute a 2D free-energy surface (FES) from 2D samples stored in .npy.")
    parser.add_argument("--in", dest="infile", required=True, help="Input .npy file containing 2D points.")
    parser.add_argument("--out_prefix", required=True, help="Output prefix (saves <prefix>.npz and <prefix>.png).")

    parser.add_argument("--bins", type=int, default=80, help="Histogram bins per dimension (default: 80).")
    parser.add_argument("--eps", type=float, default=1e-12, help="Small smoothing value to avoid log(0) (default: 1e-12).")

    parser.add_argument("--kT", type=float, default=1.0, help="Thermal energy scale (default: 1.0).")
    parser.add_argument("--xlim", type=float, nargs=2, default=None, help="Optional x-axis range: xmin xmax.")
    parser.add_argument("--ylim", type=float, nargs=2, default=None, help="Optional y-axis range: ymin ymax.")

    args = parser.parse_args()

    infile = Path(args.infile)
    out_prefix = Path(args.out_prefix)

    pts = load_points(infile)

    # Decide histogram range.
    rng = pick_range(pts, args.xlim, args.ylim)
    xmin, xmax, ymin, ymax = rng

    # 2D histogram of counts.
    counts, xedges, yedges = np.histogram2d(
        pts[:, 0],
        pts[:, 1],
        bins=args.bins,
        range=[[xmin, xmax], [ymin, ymax]],
        density=False,
    )

    # Add epsilon so no bin is exactly zero (avoids log(0)).
    counts = counts + args.eps

    # Convert counts to probability P(x,y) by dividing by total counts.
    P = counts / counts.sum()

    # Free energy in "kT units" if kT=1:
    # F = -kT * ln(P)
    F = -float(args.kT) * np.log(P)

    # Shift so minimum is 0 (common plotting convention).
    F = F - F.min()

    # Compute bin centers for x and y (useful for plotting / saving).
    xcenters = 0.5 * (xedges[:-1] + xedges[1:])
    ycenters = 0.5 * (yedges[:-1] + yedges[1:])

    # Save raw grid data for later reuse.
    out_npz = out_prefix.with_suffix(".npz")
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        str(out_npz),
        F=F,
        P=P,
        xcenters=xcenters,
        ycenters=ycenters,
        xedges=xedges,
        yedges=yedges,
        meta=dict(bins=args.bins, eps=args.eps, kT=args.kT, infile=str(infile)),
    )
    print(f"Saved grid data: {out_npz}")

    # Plot and save an image if matplotlib is available.
    out_png = out_prefix.with_suffix(".png")
    if plt is None:
        print("[WARN] matplotlib not installed, skipping PNG plot. Install matplotlib to enable plotting.")
        return

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)

    # We plot F as an image.
    # Important: histogram2d returns array indexed as [x_bin, y_bin], so we transpose for correct orientation.
    im = ax.imshow(
        F.T,
        origin="lower",
        extent=[xmin, xmax, ymin, ymax],
        aspect="auto",
    )

    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("2D Free Energy Surface (shifted so min=0)")

    fig.colorbar(im, ax=ax, label="Free energy (same units as kT)")

    fig.tight_layout()
    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)

    print(f"Saved plot: {out_png}")


if __name__ == "__main__":
    main()
