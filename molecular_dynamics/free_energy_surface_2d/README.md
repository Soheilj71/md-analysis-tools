# heatmap.py

A general-purpose command-line tool for generating 2-D density heatmaps from NumPy `.npy` files.  
Drop in any array — point clouds, trajectories, or image grids — and get a publication-quality figure with one command.

---

## Features

- **Zero configuration required** — shape is detected automatically
- Three plot styles: **hexbin**, **hist2d**, and **imshow**
- Handles 6 array shapes out of the box (see below)
- Logarithmic density scale via `--log`
- Fully configurable: colormap, bins, axis labels, limits, figure size, DPI, output path
- Output filename defaults to `<input_stem>_heatmap.png` next to the input file

---

## Requirements

```
numpy
matplotlib
```

Install with:

```bash
pip install numpy matplotlib
```

---

## Usage

```bash
python heatmap.py <input.npy> [options]
```

### Minimal examples

```bash
# Auto-detect shape, save train_x0_heatmap.png
python heatmap.py train_x0.npy

# Trajectory array (N, T, 1, 2) — flattened into a point cloud, log scale
python heatmap.py synthetic_trajs.npy --kind hexbin --cmap viridis --log --gridsize 80

# 2-D histogram, 120 bins per axis, logarithmic norm
python heatmap.py train_x1.npy --kind hist2d --bins 120 --log

# Wide array — choose which two columns to use as x and y
python heatmap.py data.npy --xcol 2 --ycol 5

# Custom title, axis labels, and output path
python heatmap.py train_md_traj.npy \
    --title "MD Trajectory Density" \
    --xlabel "x (Å)" --ylabel "y (Å)" \
    --output figures/md_density.png

# 2-D grid array rendered with imshow
python heatmap.py grid.npy --kind imshow --cmap inferno
```

---

## Supported array shapes

| Shape | Interpretation |
|---|---|
| `(N, 2)` | N 2-D points; columns are x and y |
| `(N, D)` with D > 2 | Wide array; pick columns with `--xcol` / `--ycol` |
| `(N, T, 2)` | Trajectory with T time-steps; all steps flattened |
| `(N, T, 1, 2)` | Same with a singleton spatial dim (common in diffusion models) |
| `(H, W)` | 2-D grid or image; rendered directly with `imshow` |
| `(N,)` | 1-D array; plotted as index vs. value |

---

## All options

| Flag | Default | Description |
|---|---|---|
| `input` | — | Path to the `.npy` file *(required)* |
| `--kind` | `auto` | Plot type: `hexbin`, `hist2d`, `imshow`, or `auto` |
| `--cmap` | `plasma` | Any [Matplotlib colormap](https://matplotlib.org/stable/gallery/color/colormap_reference.html) |
| `--gridsize` | `100` | Hex-grid cell count (hexbin only) |
| `--bins` | `100` | Bins per axis (hist2d only) |
| `--log` | off | Use logarithmic density scale |
| `--no-colorbar` | off | Hide the colorbar |
| `--title` | filename | Figure title |
| `--xlabel` | — | X-axis label |
| `--ylabel` | — | Y-axis label |
| `--xlim MIN MAX` | — | X-axis limits |
| `--ylim MIN MAX` | — | Y-axis limits |
| `--xcol` | `0` | Column index for x (wide arrays) |
| `--ycol` | `1` | Column index for y (wide arrays) |
| `--figsize W H` | `6 5` | Figure size in inches |
| `--dpi` | `150` | Output resolution |
| `-o / --output` | `<stem>_heatmap.png` | Output file path |

---

## Example outputs

| Input | Command | Result |
|---|---|---|
| `train_x0.npy` `(14996, 2)` | `python heatmap.py train_x0.npy` | hexbin, plasma |
| `train_x1.npy` `(14996, 2)` | `... --kind hist2d --log` | hist2d, log norm |
| `synthetic_trajs.npy` `(10, 10, 501, 2)` | `... --log --gridsize 80` | 100 200 time-steps flattened |
| `train_md_traj.npy` `(15001, 2)` | `... --title "MD density"` | hexbin, custom title |

---

## License

MIT
