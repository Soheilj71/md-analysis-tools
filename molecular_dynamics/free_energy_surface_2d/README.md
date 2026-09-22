# 2D Free Energy Surface from Point Data

A simple Python script to compute a **2D free energy surface (FES)** from sampled 2D data stored in a NumPy file (`.npy`).

This tool:

- loads 2D points from a NumPy file
- builds a 2D histogram
- converts the probability distribution into a free energy surface
- shifts the minimum free energy to zero
- saves both the numerical grid and a plotted image

It is useful for people working with:

- molecular dynamics
- reduced-dimensional trajectories
- latent-space analysis
- reaction coordinates
- probability-to-free-energy conversion

---

## What this script does

The script reads 2D sampled points and estimates the probability distribution \( P(x, y) \) using a 2D histogram.

It then converts the probability into free energy using:


$$
F(x, y) = -kT \ln P(x, y)
$$

Finally, it shifts the surface so that the minimum free energy is zero:

$$
F_{\text{shifted}}(x, y) = F(x, y) - \min(F)
$$

This is a common convention in scientific plotting because it makes the lowest-energy region equal to 0.

---

## Input format

The script accepts a NumPy `.npy` file in one of these shapes:

### 1. Flat 2D point array
```python
(N, 2)
```
Example:
* `N` rows
* 2 columns
* first column = `x`
* second column = `y`

### 2. Trajectory-style array
```python
(n_traj, n_steps, 2)
```

Example:
* multiple trajectories
* multiple time steps per trajectory
* 2 coordinates per point
The script automatically flattens this into shape `(N, 2)` before processing.

# Output files
If you use:
```bash
--out_prefix results/fes_output
```

the script saves:

## 1. Numerical grid
```bash
results/fes_output.npz
```

This compressed NumPy file contains:
* `F` → free energy grid
* `P` → probability grid
* `xcenters` → x bin centers
* `ycenters` → y bin centers
* `xedges` → x bin edges
* `yedges` → y bin edges
* `meta` → metadata such as number of bins, epsilon, kT, and input filename
  
## 2. Plot image
```bash
results/fes_output.png
```

This is a heatmap of the 2D free energy surface.

# Requirements
## Python
*  Python 3.8 or newer is recommended

## Required package
*  `numpy`

## Optional package
*  `matplotlib`
   Only needed if you want the PNG plot.

Install dependencies with:
```bash
pip install numpy matplotlib
```

If `matplotlib` is not installed, the script will still save the `.npz` file, but it will skip the PNG plot.

# Usage

Basic usage:

```bash
python fes_2d_from_points.py --in points.npy --out_prefix output/fes
```

Example with custom number of bins and thermal energy:
```bsah
python fes_2d_from_points.py \
  --in points.npy \
  --out_prefix output/fes \
  --bins 100 \
  --kT 1.0
```

Example with manual axis limits:
```bash
python fes_2d_from_points.py \
  --in points.npy \
  --out_prefix output/fes \
  --xlim -3 3 \
  --ylim -2 2
```

# Command-line arguments
## Required arguments
`--in`
Path to the input `.npy` file.

Example:
```bash
--in data/points.npy
```

`--out_prefix`

Prefix for output files.

Example:
```bash
--out_prefix results/fes_run1
```

This creates:
*    `results/fes_run1.npz`
*    `results/fes_run1.png`

## Optional arguments
`--bins`
Number of histogram bins per dimension.
Default:
```bash
80
```

Larger values give finer resolution, but may require more data for a stable surface.
Example:
```bash
--bins 120
```

```
--eps
```

A small number added to every histogram bin to avoid log(0).
Default:
```bash
1e-12
```

This helps prevent numerical problems in low-probability regions.
Example:
```bash
--eps 1e-10
```

`--kT`

Thermal energy factor used in the free energy equation.
Default:
```bash
1.0
```

If `kT = 1`, the free energy is reported in reduced units.

Example:
```bash
--kT 0.593
```

`--xlim`

Optional x-axis range as:
```bash
--xlim xmin xmax
```

Example:
```bash
--xlim -4 4
```

`--ylim`

Optional y-axis range as:
```bash
--ylim ymin ymax
```

Example:
```bash
--ylim -3 3
```

# Example workflow
## Example 1: Basic run
```bash
python fes_2d_from_points.py --in sample.npy --out_prefix results/fes
```

## Example 2: Higher-resolution histogram
```bash
python fes_2d_from_points.py --in sample.npy --out_prefix results/fes --bins 150
```

# Example 3: Fixed plotting region
```bash
python fes_2d_from_points.py \
  --in sample.npy \
  --out_prefix results/fes \
  --xlim -2.5 2.5 \
  --ylim -2.5 2.5
```

# How the method works

The script follows these steps:
1.  Load input points
    *    reads a `.npy` file
    *    accepts either `(N, 2)` or `(n_traj, n_steps, 2)`

2.  Clean the data
    *    removes rows containing `NaN` or `inf`

3.  Choose the histogram range
    *    uses user-defined `xlim` and `ylim` if provided
    *    otherwise automatically chooses a range from the data with a small padding

4.  Build a 2D histogram
    *    counts how many points fall into each bin

5.  Convert counts to probability
    *    normalizes the histogram so all bins sum to 1

6. Convert probability to free energy
    *    uses:
          $F = -kT \ln(P)$

7.  Shift the minimum energy to zero
    *    makes the lowest point of the surface equal to 0

8.  Save results
    *    stores the grid in `.npz`
    *    saves a PNG plot if `matplotlib` is available

# Notes and interpretation
## Why add epsilon?

Some bins may contain zero counts. Since:

$$
\ln(0)
$$

is undefined, the script adds a very small value (`eps`) to all bins before taking the logarithm.

## Why shift the minimum to zero?

Free energy surfaces are often shown relative to the lowest-energy state. This makes plots easier to interpret.

## Why can the result be noisy?
If you use:
*    too few points
*    too many bins
*    poor sampling
the estimated free energy surface may look rough or unstable.

# Limitations
*    This script assumes the input data already represents meaningful 2D coordinates.
*    It uses simple histogram-based density estimation, not kernel density estimation.
*    The free energy quality depends strongly on sampling quality and histogram settings.
*    Very sparse data may produce unstable surfaces.
*    The axis labels are generic (`x` and `y`) and may need editing for publication-quality figures.

# Error handling
The script stops with a clear error message if:
*    The input file does not exist
*    The input shape is not `(N, 2)` or `(n_traj, n_steps, 2)`
*    Too few valid points remain after cleaning

The script also warns if `matplotlib` is missing and skips the PNG plot in that case.

# Example file structure
```bash
project/
├── fes_2d_from_points.py
├── data/
│   └── points.npy
└── results/
```
Run:
```bash
python fes_2d_from_points.py --in data/points.npy --out_prefix results/fes
```

Expected output:

```bash
results/fes.npz
results/fes.png
```

# Possible future improvements
Some useful future extensions could include:
*    contour plotting
*    custom axis labels
*    custom colormap selection
*    support for CSV input
*    support for kernel density estimation
*    optional energy cutoff for visualization
*    saving raw histogram counts separately

