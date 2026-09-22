# Universal Dihedral Angle Calculator (MDAnalysis)

This repository provides a **universal Python script** to calculate dihedral angles from molecular dynamics simulations using **MDAnalysis**.

It works across many MD engines (as long as MDAnalysis supports the input files), including:

- **GROMACS** (e.g., `.tpr + .xtc`)
- **NAMD / CHARMM** (e.g., `.psf + .dcd`)
- **AMBER** (e.g., `.prmtop + .nc`)
- **Generic** structure + trajectory formats (`.pdb`, `.gro`, `.dcd`, `.trr`, etc.)

---

## What the Script Can Do

### 1) Protein Backbone Dihedrals (Automatic)
Computes backbone angles for all protein residues:

- **Phi (ϕ)**: `C(i−1) – N(i) – CA(i) – C(i)`
- **Psi (ψ)**: `N(i) – CA(i) – C(i) – N(i+1)`
- **Omega (ω)**: `CA(i) – C(i) – N(i+1) – CA(i+1)`

✅ In this mode, you do **not** need to provide atoms.

---

### 2) Custom Dihedrals (Any 4 Atoms)
Compute any torsion you want by defining **four atom selections**:

Examples:
- Side-chain torsions (chi angles)
- Ligand torsions
- Special/modified residues
- Any arbitrary 4-atom torsion

You can define **multiple torsions** by repeating `--torsion`.

---

## Requirements

Install dependencies:

```bash
pip install numpy MDAnalysis
```
Python version: 3.8+

# Usage
## A) Backbone mode (recommended)
## GROMACS example

```bash
python dihedrals_universal.py -t topol.tpr -x traj.xtc -o dihedrals.npz
```

## NAMD example
```bash
python dihedrals_universal.py -t system.psf -x traj.dcd -o dihedrals.npz
```

Optional CSV output (only for small systems):
```bash
python dihedrals_universal.py -t topol.tpr -x traj.xtc -o dihedrals.npz --csv dihedrals.csv
```

## B) Custom torsion mode (any 4 atoms)

Custom torsions are specified like this:
```
--torsion "NAME: SEL1 | SEL2 | SEL3 | SEL4"
```

Where `EL1..SEL4` are MDAnalysis selection strings, and each must match exactly one atom.
Example (chi1-like torsion for residue 10):
```python
python dihedrals_universal.py -t topol.tpr -x traj.xtc -o dihedrals.npz \
  --torsion "chi1_res10: (resid 10 and name N) | (resid 10 and name CA) | (resid 10 and name CB) | (resid 10 and name CG)"
```

Multiple torsions:
```bash
python dihedrals_universal.py -t topol.tpr -x traj.xtc -o dihedrals.npz \
  --torsion "t1: (resid 10 and name N) | (resid 10 and name CA) | (resid 10 and name CB) | (resid 10 and name CG)" \
  --torsion "t2: (resid 25 and name N) | (resid 25 and name CA) | (resid 25 and name CB) | (resid 25 and name CG)"
```

# Output Files
## 1) NPZ output (recommended)
The `.npz` file stores:
   * time
   * backbone arrays:
      * `phi_deg`, `psi_deg`, `omega_deg`
      * `phi_meta`, `psi_meta`, `omega_meta`
   * custom torsions:
      * `custom_torsion_names`
      * `custom_torsion_deg`
Load it in Python:
```python
import numpy as np
data = np.load("dihedrals.npz", allow_pickle=True)

time = data["time"]

# Backbone (if computed)
phi = data.get("phi_deg", None)
psi = data.get("psi_deg", None)
omega = data.get("omega_deg", None)

# Custom torsions (if provided)
names = data.get("custom_torsion_names", None)
angles = data.get("custom_torsion_deg", None)
```

## 2) CSV output (optional)
CSV is saved in a wide format:
   * one row per frame
   * many columns (one per dihedral)

⚠️ CSV can become extremely large for large proteins or long trajectories.
For serious work, use NPZ.

# Troubleshooting
## Error: “Selection must match exactly 1 atom”
Your custom selection matched 0 atoms or multiple atoms.

Fix by making it more specific, e.g.:
   * add `segid A`
   * add `resid 10`
   * ensure `name CA` etc.

Example:
```
(segid A and resid 10 and name CA)
```

# Citation
If you use this script in research, please cite MDAnalysis:
   * Michaud-Agrawal et al., J. Comput. Chem. (2011)
   * Gowers et al., SciPy Proceedings (2016)
