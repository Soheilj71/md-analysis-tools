# md-analysis-tools

Scripts for molecular dynamics analysis, machine learning on MD data, GROMACS plotting, and HPC/Slurm job management.

---

## molecular_dynamics/

| Script | Language | Description |
|--------|----------|-------------|
| [dihedral_angle_calculation](molecular_dynamics/dihedral_angle_calculation/) | Python | Compute backbone and side-chain dihedral angles from MD trajectories |
| [free_energy_surface_2d](molecular_dynamics/free_energy_surface_2d/) | Python | Build 2D free energy surfaces from `.npy` coordinate arrays |
| [kl_divergence_bootstrapping](molecular_dynamics/kl_divergence_bootstrapping/) | Python | KL divergence with bootstrapped confidence intervals between two MD ensembles |
| [muller_potential_2d](molecular_dynamics/muller_potential_2d/) | Python | Müller-Brown potential energy surface for 2D sampling benchmarks |
| [pdb_standardizer](molecular_dynamics/pdb_standardizer/) | Python | Strict PDB formatter with field-level validation and logging |
| [tica_calculation](molecular_dynamics/tica_calculation/) | Python | Compute time-lagged independent components (TICs) from MD trajectories |


## machine_learning/

| Script | Language | Description |
|--------|----------|-------------|
| [find_best_checkpoint](machine_learning/find_best_checkpoint/) | Python | Scans PyTorch Lightning `metrics.csv` logs and symlinks the best checkpoint |
| [kl_divergence](machine_learning/kl_divergence/) | Python | 2D KL divergence between two datasets using kernel density estimation |
| [kl_divergence_bootstrapping](machine_learning/kl_divergence_bootstrapping/) | Python | KL divergence with bootstrapped confidence intervals |
| [Bootstrapping](machine_learning/Bootstrapping/) | Python | Bootstrapping utility for computing confidence intervals on arbitrary metrics |

## plotting/

| Script | Language | Description |
|--------|----------|-------------|
| [xvg_line_graph](plotting/xvg_line_graph/) | Python | Plot GROMACS `.xvg` files as line graphs |
| [xvg_scatter_line](plotting/xvg_scatter_line/) | Python | Plot GROMACS `.xvg` files as combined scatter + line time series |

## hpc/

| Script | Language | Description |
|--------|----------|-------------|
| [check_queue](hpc/check_queue/) | Bash | Show your Slurm jobs with readable status summary |
| [slurm_array_template](hpc/slurm_array_template/) | Bash | Ready-to-use Slurm array job template |
| [submit_many_jobs](hpc/submit_many_jobs/) | Bash | Submit `sbatch` jobs across many folders in one command |
| [run_slurm_every_folder](hpc/run_slurm_every_folder/) | Bash | Run a Slurm job inside every simulation subfolder (range or list mode) |
| [search_slurm_logs](hpc/search_slurm_logs/) | Bash | Search Slurm output logs for best metric values |
| [gather_files](hpc/gather_files/) | Bash | Collect files matching a pattern from a directory tree into one place |
| [lineforge](hpc/lineforge/) | Bash | Safe batch line replacement across files (dry-run, backup, regex support) |

---

## Requirements

```bash
pip install -r requirements.txt
```

The Bash scripts have no Python dependencies. They require Bash and a Slurm-enabled HPC cluster for the `hpc/` scripts.
