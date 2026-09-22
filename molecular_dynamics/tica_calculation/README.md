# TICA Analysis for MD Trajectories

**Time-lagged Independent Component Analysis (TICA)** is the standard first step
for identifying the **slowest collective motions** in molecular dynamics simulations.
This repository provides a general-purpose script that works for any protein — from
small peptides to large multi-domain systems.

---

## What TICA does

TICA finds linear combinations of input features (torsion angles, distances, …) that
maximise the **autocorrelation at a chosen lag time** τ.  The first few components
(TIC 1, TIC 2, …) capture the slowest, most biologically relevant conformational
changes.  The script also tells you **how many TICs are meaningful** using the
implied-timescales criterion (see below).

---

## Features

| Capability | Details |
|---|---|
| **Featurizations** | φ/ψ torsions · φ/ψ/ω backbone · pairwise Cα distances · pre-computed `.npy` |
| **Validation** | Implied-timescales scan with "above/below diagonal" annotation |
| **Kinetic variance** | Per-TIC and cumulative scree plot |
| **FES plots** | 2-D free-energy surface for any pair of TICs |
| **Projection histograms** | 1-D distributions, coloured by meaningful vs. noise |
| **Saved outputs** | Feature array, TICA model, coordinates, summary text |
| **Multiple replicates** | Pass several `--traj` files; they are concatenated automatically |

---

## Requirements

```bash
# recommended: conda environment
conda create -n tica python=3.10
conda activate tica
conda install -c conda-forge mdtraj
pip install deeptime numpy matplotlib
```

---

## Quick start

### Alanine dipeptide (or any small peptide) — φ/ψ torsions

```bash
python tica_general.py \
    --pdb  protein.pdb \
    --traj traj_R1.xtc traj_R2.xtc traj_R3.xtc \
    --feature phi_psi \
    --lagtime 10 \
    --dim 4 \
    --out-dir results/
```

### Larger protein — Cα distances, 6 TICs, custom lag

```bash
python tica_general.py \
    --pdb  1abc.pdb \
    --traj production.xtc \
    --feature ca_distances \
    --lagtime 50 \
    --dim 6 \
    --its-lags 5,10,20,50,100,200,500 \
    --out-dir results_1abc/
```

### Pre-computed feature array (skip trajectory loading)

```bash
python tica_general.py \
    --feature custom \
    --feature-file my_features.npy \
    --lagtime 20 \
    --dim 4
```

### All backbone dihedrals (φ, ψ, ω) — richer representation

```bash
python tica_general.py \
    --pdb protein.pdb \
    --traj traj.xtc \
    --feature backbone \
    --dim 6
```

---

## All options

```
Input:
  --pdb FILE              Topology PDB file
  --traj FILE [FILE ...]  Trajectory file(s) — multiple files = replicates
  --feature {phi_psi, backbone, ca_distances, custom}
                          Featurization type (default: phi_psi)
  --feature-file FILE     .npy file for --feature custom

TICA parameters:
  --lagtime INT           Lag time in frames (default: 10)
  --dim INT               Number of TIC components (default: 4)
  --subsample INT         Max frames for fitting (default: 500,000)

Implied-timescales scan:
  --its-lags INT,INT,...  Lag times to scan (default: 1,2,5,10,20,50,100,150,200)
  --skip-its              Skip the scan (faster, no quality info)

Output:
  --out-dir DIR           Output directory (default: tica_output/)
  --title STR             Title string on all plots
  --bins INT              Bins for FES histogram (default: 100)
  --fes-pairs I,J[;I,J]   TIC pairs for FES plots, 0-based (default: 0,1)
  --no-projections        Skip 1-D projection histograms
```

---

## Understanding the outputs

```
tica_output/
├── features.npy                  All featurized frames (N × n_feat)
├── tica_model.npz                Saved TICA eigenvectors & singular values
├── tica_coords.npy               TIC coordinates (N × dim)
├── tica_coords_per_traj.npy      Per-trajectory TIC arrays
├── tica_implied_timescales.png   ← KEY: which TICs are meaningful?
├── tica_kinetic_variance.png     Scree plot of kinetic variance
├── tica_fes_IC1_IC2.png          2-D free-energy surface
├── tica_projections.png          1-D histograms per TIC
└── tica_summary.txt              Plain-text numbers summary
```

---

## How to tell which TICs are meaningful

The **implied-timescales plot** (`tica_implied_timescales.png`) is the main
diagnostic.

```
Implied timescale
     │       ●──●──●  TIC 1  ← ABOVE diagonal: slow, meaningful
     │      ●──●──●   TIC 2  ← ABOVE diagonal: meaningful
     │  ●──●──●       TIC 3  ← collapses onto diagonal: NOT meaningful
     │──────────────  diagonal (timescale = lag)
     └──────────────► Lag time
```

**Rule:** A TIC is meaningful if its implied timescale lies **above the diagonal**
(timescale > lag time) across the lag scan.  When a curve converges onto or
drops below the diagonal, that component no longer captures a distinct slow process —
it is dominated by noise or by the lag time itself.

The script:
1. Draws the diagonal as a black dashed line.
2. Shades the "below diagonal" region in gray.
3. Draws meaningful TICs in solid bold lines and noise TICs in dashed faint lines.
4. Annotates the plot title with the count: *"Meaningful TICs: 2 of 4"*.
5. Writes the same information to `tica_summary.txt`.

---

## Choosing the lag time

The lag time τ should be:
- **Short enough** that the trajectory has many independent lag-time windows
  (rule of thumb: total frames ≫ 10 × τ).
- **Long enough** that the implied timescales have plateaued on the ITS plot
  (the curves flatten out before reaching the diagonal).

Start with a short lag (e.g. 10 frames) and inspect `tica_implied_timescales.png`.
If timescales are still rising steeply, increase τ.

---

## Choosing the number of TIC dimensions

Set `--dim` to a number **larger than you expect** (e.g. 6–8), then let the
implied-timescales plot tell you how many are truly meaningful.  Only the
meaningful TICs should be used for downstream analyses (MSM building, FES,
diffusion model training, etc.).

---

## Featurization guide

| Protein type | Recommended feature |
|---|---|
| Small peptide (≤ 10 res) | `phi_psi` |
| Medium protein, backbone focus | `backbone` |
| Large protein / folding | `ca_distances` |
| Custom pipeline / coarse-grained | `custom` + `--feature-file` |

---

## Reusing the fitted model on new data

```python
import numpy as np
from deeptime.decomposition import TICA

# Load saved model
d = np.load("tica_output/tica_model.npz")

# Transform new features
new_feats = np.load("new_features.npy")   # shape (T, n_feat)
# Manually apply: TIC coords = (new_feats - mean) @ singular_vectors_left
new_tic = (new_feats - d["mean_0"]) @ d["singular_vectors_left"]
```

---

## Citation

If you use this script in a publication, please cite:

- **MDTraj**: McGibbon et al., *Biophys. J.* **109**, 1528–1532 (2015).
- **deeptime**: Hoffmann et al., *Mach. Learn.: Sci. Technol.* **3**, 015009 (2022).
- **TICA theory**: Pérez-Hernández et al., *J. Chem. Phys.* **139**, 015102 (2013).

---

## License

MIT — free to use, modify, and distribute.
