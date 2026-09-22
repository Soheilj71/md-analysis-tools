# TICA Analysis for MD Trajectories

**Time-lagged Independent Component Analysis (TICA)** is the standard first step
for identifying the **slowest collective motions** in molecular dynamics simulations.
This script works with any trajectory format supported by MDTraj (XTC, DCD, TRR, NC, …)
and any filename — no directory structure or naming convention required.

---

## What TICA does

TICA finds linear combinations of input features (torsion angles) that maximise the
**autocorrelation at a chosen lag time** τ. The first few components (TIC 1, TIC 2, …)
capture the slowest, most biologically relevant conformational changes. The script also
tells you **how many TICs are meaningful** using the implied-timescales criterion.

---

## Requirements

```bash
conda create -n tica python=3.10
conda activate tica
conda install -c conda-forge mdtraj
pip install deeptime numpy matplotlib
```

---

## Quick start

### Single trajectory — DCD format

```bash
python tica_analysis.py \
    --pdb  ala2.pdb \
    --traj ala2.dcd \
    --lagtime 10 \
    --dim 2 \
    --out-dir results/ala2
```

### Single trajectory — XTC format

```bash
python tica_analysis.py \
    --pdb  protein.pdb \
    --traj production.xtc \
    --lagtime 10 \
    --dim 2 \
    --out-dir results/protein
```

### Multiple replicates (any format)

```bash
python tica_analysis.py \
    --pdb  protein.pdb \
    --traj R1.dcd R2.dcd R3.dcd \
    --lagtime 50 \
    --dim 4 \
    --out-dir results/protein
```

---

## All options

```
Input:
  --pdb  FILE             Topology PDB file (any path/name)
  --traj FILE [FILE ...]  Trajectory file(s): xtc, dcd, trr, nc, …
                          Pass multiple files for replicates

TICA parameters:
  --lagtime INT           Lag time in frames (default: 10)
  --dim INT               Number of TIC components (default: 2)
  --subsample INT         Max frames for fitting (default: 500,000)

Implied-timescales scan:
  --its-lags INT,INT,...  Lag times to scan (default: 1,2,5,10,20,50,100,150,200)
  --skip-its              Skip the scan (faster, no quality info)

Output:
  --out-dir DIR           Output directory (default: tica_output)
  --title STR             Title for plots (default: PDB filename)
  --bins INT              Bins for FES histogram (default: 100)
```

---

## Outputs

```
tica_output/
├── phi_psi.npy                   Raw phi/psi angles per trajectory
├── tica_coords.npy               TIC coordinates, all frames (N × dim)
├── tica_coords_per_traj.npy      Per-trajectory TIC arrays
├── tica_model.npz                Saved TICA eigenvectors & singular values
├── tica_fes.png                  2-D free-energy surface (TIC1 vs TIC2)
└── tica_implied_timescales.png   Timescales vs lag — tells you which TICs are meaningful
```

---

## How to tell which TICs are meaningful

The **implied-timescales plot** (`tica_implied_timescales.png`) is the main diagnostic.

**Rule:** A TIC is meaningful if its implied timescale lies **above the diagonal**
(timescale > lag time) across the lag scan. When a curve collapses onto or drops below
the diagonal, that component is dominated by noise.

---

## Choosing the lag time

- **Too short**: timescales on the ITS plot are still rising steeply — increase τ.
- **Too long**: too few independent windows — decrease τ.

Start with `--lagtime 10`, inspect `tica_implied_timescales.png`, and adjust.

---

## Reusing the fitted model on new data

```python
import numpy as np

d = np.load("tica_output/tica_model.npz")
new_feats = np.load("new_features.npy")   # shape (T, n_feat)
new_tic = (new_feats - d["mean_0"]) @ d["singular_vectors_left"]
```

---

## Citation

- **MDTraj**: McGibbon et al., *Biophys. J.* **109**, 1528–1532 (2015).
- **deeptime**: Hoffmann et al., *Mach. Learn.: Sci. Technol.* **3**, 015009 (2022).
- **TICA theory**: Pérez-Hernández et al., *J. Chem. Phys.* **139**, 015102 (2013).

---

## License

MIT — free to use, modify, and distribute.
