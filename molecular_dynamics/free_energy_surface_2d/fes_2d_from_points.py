"""
heatmap.py — General-purpose 2-D density heatmap for NumPy arrays.

Supported array shapes
----------------------
(N, 2)               — N points, columns are x / y
(N, D) with D > 2    — pick two columns with --xcol / --ycol  (default 0, 1)
(N, T, 2)            — trajectory: flatten all time-steps into one point cloud
(N, T, 1, 2)         — same with an extra singleton dim (e.g. Dr. Chen's format)
(H, W)               — 2-D grid / image: rendered directly with imshow
(N,)                 — 1-D array: plotted as a histogram (row index vs value)

Usage examples
--------------
# quickest call — auto-detects shape, saves heatmap.png next to the .npy file
python heatmap.py train_x0.npy

# trajectory array, log-density, plasma colourmap, 80-cell grid
python heatmap.py synthetic_trajs.npy --kind hexbin --cmap plasma --log --gridsize 80

# 2-D point cloud, histogram style, custom output
python heatmap.py train_x1.npy --kind hist2d --bins 120 --output out.png --title "X1 density"

# pick specific columns from a wide array
python heatmap.py data.npy --xcol 2 --ycol 5

# 2-D grid array rendered as an image
python heatmap.py grid.npy --kind imshow --cmap viridis
"""

import argparse
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np


# ---------------------------------------------------------------------------
# Shape normalisation
# ---------------------------------------------------------------------------

def extract_xy(arr: np.ndarray, xcol: int, ycol: int):
    """
    Return (x, y, mode) where mode is 'scatter' or 'grid'.

    'scatter' → x and y are flat 1-D arrays of equal length, ready for hexbin/hist2d.
    'grid'    → arr is returned as-is for imshow.
    """
    arr = np.asarray(arr, dtype=float)
    ndim = arr.ndim

    # ---- 2-D grid (H × W) --------------------------------------------------
    if ndim == 2 and arr.shape[1] != 2:
        # Likely a grid image, not a point cloud
        return arr, None, "grid"

    # ---- 1-D array ---------------------------------------------------------
    if ndim == 1:
        return np.arange(len(arr), dtype=float), arr.flatten(), "scatter"

    # ---- (N, 2) point cloud ------------------------------------------------
    if ndim == 2 and arr.shape[1] == 2:
        return arr[:, 0], arr[:, 1], "scatter"

    # ---- (N, D) wide array with D > 2 -------------------------------------
    if ndim == 2 and arr.shape[1] > 2:
        return arr[:, xcol], arr[:, ycol], "scatter"

    # ---- (N, T, 2) trajectory ----------------------------------------------
    if ndim == 3 and arr.shape[-1] == 2:
        flat = arr.reshape(-1, 2)
        return flat[:, 0], flat[:, 1], "scatter"

    # ---- (N, T, 1, 2) trajectory (Dr. Chen / i2sb format) -----------------
    if ndim == 4 and arr.shape[-1] == 2:
        flat = arr.reshape(-1, 2)
        return flat[:, 0], flat[:, 1], "scatter"

    # ---- fallback: treat last two dims as x / y ----------------------------
    flat = arr.reshape(-1, arr.shape[-1])
    if flat.shape[1] >= max(xcol, ycol) + 1:
        return flat[:, xcol], flat[:, ycol], "scatter"

    raise ValueError(
        f"Cannot extract x/y from array with shape {arr.shape}. "
        "Try specifying --xcol and --ycol explicitly."
    )


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------

def plot_hexbin(ax, x, y, gridsize, cmap, log, colorbar):
    scale = "log" if log else None
    hb = ax.hexbin(x, y, gridsize=gridsize, cmap=cmap, bins=scale)
    if colorbar:
        cb = plt.colorbar(hb, ax=ax)
        cb.set_label("log(count)" if log else "count")
    return hb


def plot_hist2d(ax, x, y, bins, cmap, log, colorbar):
    norm = LogNorm() if log else None
    _, _, _, img = ax.hist2d(x, y, bins=bins, cmap=cmap, norm=norm)
    if colorbar:
        cb = plt.colorbar(img, ax=ax)
        cb.set_label("log(count)" if log else "count")
    return img


def plot_imshow(ax, grid, cmap, log, colorbar):
    data = np.log1p(grid) if log else grid
    im = ax.imshow(data, cmap=cmap, origin="lower", aspect="auto")
    if colorbar:
        cb = plt.colorbar(im, ax=ax)
        cb.set_label("log(1 + value)" if log else "value")
    return im


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="Generate a 2-D density heatmap from a .npy file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", help="Path to the .npy file.")
    p.add_argument(
        "--kind",
        choices=["hexbin", "hist2d", "imshow", "auto"],
        default="auto",
        help=(
            "Plot type. 'auto' picks hexbin for scatter data and imshow for 2-D grids "
            "(default: auto)."
        ),
    )
    p.add_argument("--cmap", default="plasma", help="Matplotlib colourmap (default: plasma).")
    p.add_argument("--gridsize", type=int, default=100, help="Hex grid resolution (default: 100).")
    p.add_argument("--bins", type=int, default=100, help="Histogram bin count per axis (default: 100).")
    p.add_argument("--log", action="store_true", help="Use logarithmic density scale.")
    p.add_argument("--no-colorbar", dest="colorbar", action="store_false", help="Hide the colorbar.")
    p.set_defaults(colorbar=True)
    p.add_argument("--title", default=None, help="Figure title (default: input filename).")
    p.add_argument("--xlabel", default=None, help="X-axis label.")
    p.add_argument("--ylabel", default=None, help="Y-axis label.")
    p.add_argument("--xlim", nargs=2, type=float, metavar=("MIN", "MAX"), help="X-axis limits.")
    p.add_argument("--ylim", nargs=2, type=float, metavar=("MIN", "MAX"), help="Y-axis limits.")
    p.add_argument("--xcol", type=int, default=0, help="Column index for x (wide arrays, default: 0).")
    p.add_argument("--ycol", type=int, default=1, help="Column index for y (wide arrays, default: 1).")
    p.add_argument("--figsize", nargs=2, type=float, metavar=("W", "H"), default=[6, 5], help="Figure size in inches (default: 6 5).")
    p.add_argument("--dpi", type=int, default=150, help="Output DPI (default: 150).")
    p.add_argument("--output", "-o", default=None, help="Output file path (default: <input_stem>_heatmap.png).")
    return p


def main():
    args = build_parser().parse_args()

    # Load ----------------------------------------------------------------
    if not os.path.isfile(args.input):
        sys.exit(f"Error: file not found — {args.input}")

    arr = np.load(args.input)
    print(f"Loaded {args.input}: shape={arr.shape}, dtype={arr.dtype}")

    # Extract coordinates -------------------------------------------------
    try:
        x, y, mode = extract_xy(arr, args.xcol, args.ycol)
    except ValueError as exc:
        sys.exit(f"Error: {exc}")

    # Resolve kind --------------------------------------------------------
    kind = args.kind
    if kind == "auto":
        kind = "imshow" if mode == "grid" else "hexbin"

    if mode == "grid" and kind in ("hexbin", "hist2d"):
        print(f"Warning: array looks like a 2-D grid — switching kind to 'imshow'.")
        kind = "imshow"

    # Default output path -------------------------------------------------
    output = args.output
    if output is None:
        stem = os.path.splitext(os.path.basename(args.input))[0]
        output = os.path.join(os.path.dirname(args.input) or ".", f"{stem}_heatmap.png")

    # Plot ----------------------------------------------------------------
    fig, ax = plt.subplots(figsize=args.figsize)

    if kind == "hexbin":
        plot_hexbin(ax, x, y, args.gridsize, args.cmap, args.log, args.colorbar)
    elif kind == "hist2d":
        plot_hist2d(ax, x, y, args.bins, args.cmap, args.log, args.colorbar)
    elif kind == "imshow":
        plot_imshow(ax, arr if mode == "grid" else x.reshape(int(len(x)**0.5), -1),
                    args.cmap, args.log, args.colorbar)

    # Labels / limits / title ---------------------------------------------
    title = args.title if args.title is not None else os.path.basename(args.input)
    ax.set_title(title)

    if args.xlabel:
        ax.set_xlabel(args.xlabel)
    if args.ylabel:
        ax.set_ylabel(args.ylabel)
    if args.xlim:
        ax.set_xlim(args.xlim)
    if args.ylim:
        ax.set_ylim(args.ylim)

    plt.tight_layout()
    plt.savefig(output, dpi=args.dpi)
    plt.close(fig)
    print(f"Saved → {output}")


if __name__ == "__main__":
    main()
