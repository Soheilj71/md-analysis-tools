"""
TICA Analysis — ATLAS trajectory entry point
---------------------------------------------
Loads ATLAS MD trajectories (.xtc + .pdb), computes backbone phi/psi
torsions with MDTraj, converts to sin/cos features, fits TICA, and
saves results and plots.

Usage:
    python analysis/tica_analysis.py \\
        --protein 1d3y_B \\
        --data-dir data \\
        --out-dir analysis/1d3y_B

    # Use only replicate R1:
    python analysis/tica_analysis.py --protein 1d3y_B --data-dir data --replicates 1

    # Custom lag time and dimensionality:
    python analysis/tica_analysis.py --protein 1d3y_B --data-dir data --lagtime 50 --dim 4

Outputs (written to --out-dir):
    phi_psi.npy                  (n_replicates, T, 2) raw phi/psi in degrees
    tica_coords.npy              (M, dim) TIC coordinates, all frames concatenated
    tica_coords_per_traj.npy     object array of (T, dim) arrays, one per replicate
    tica_model.npz               TICA model parameters (reusable for new data)
    tica_fes.png                 free energy surface in TIC1/TIC2
    tica_implied_timescales.png  slowest timescales vs lag time
"""

import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import mdtraj
except ImportError:
    sys.exit("Install mdtraj:  conda install -c conda-forge mdtraj")

try:
    from deeptime.decomposition import TICA
except ImportError:
    sys.exit("Install deeptime:  pip install deeptime")


# ---------------------------------------------------------------------------
# Trajectory loading
# ---------------------------------------------------------------------------

def load_atlas_replicates(protein: str, data_dir: str, replicates: list[int]) -> list[mdtraj.Trajectory]:
    """Load one or more ATLAS replicate trajectories for a protein."""
    base = os.path.join(data_dir, protein, protein)
    pdb_path = f"{base}.pdb"
    if not os.path.exists(pdb_path):
        sys.exit(f"PDB not found: {pdb_path}")

    trajs = []
    for r in replicates:
        xtc_path = f"{base}_prod_R{r}_fit.xtc"
        if not os.path.exists(xtc_path):
            print(f"Warning: replicate R{r} not found, skipping ({xtc_path})")
            continue
        print(f"Loading replicate R{r} …")
        traj = mdtraj.load(xtc_path, top=pdb_path)
        traj = traj.atom_slice(traj.top.select("backbone"))
        print(f"  R{r}: {traj.n_frames} frames, {traj.n_residues} residues")
        trajs.append(traj)

    if not trajs:
        sys.exit("No replicate trajectories could be loaded.")
    return trajs


def compute_phi_psi(trajs: list[mdtraj.Trajectory]) -> list[np.ndarray]:
    """
    Compute phi/psi backbone torsions for each trajectory.
    Returns a list of (T, 2) arrays in degrees. Frames with NaN
    (terminal residues missing one torsion) are dropped.
    """
    result = []
    for traj in trajs:
        _, phi = mdtraj.compute_phi(traj)   # (T, n_phi)
        _, psi = mdtraj.compute_psi(traj)   # (T, n_psi)

        # Average over residues to get one phi and one psi per frame
        phi_mean = np.nanmean(np.rad2deg(phi), axis=1)   # (T,)
        psi_mean = np.nanmean(np.rad2deg(psi), axis=1)   # (T,)

        angles = np.column_stack([phi_mean, psi_mean])    # (T, 2)
        mask = np.isfinite(angles).all(axis=1)
        result.append(angles[mask])

    return result


# ---------------------------------------------------------------------------
# TICA helpers
# ---------------------------------------------------------------------------

def to_sincos(phi_psi_deg: np.ndarray) -> np.ndarray:
    """(T, 2) degrees -> (T, 4) sin/cos features."""
    rad = np.deg2rad(phi_psi_deg)
    return np.column_stack([np.sin(rad), np.cos(rad)])


def subsample_trajs(trajs: list[np.ndarray], max_frames: int, seed: int = 42) -> list[np.ndarray]:
    total = sum(t.shape[0] for t in trajs)
    if total <= max_frames:
        return trajs
    rng = np.random.default_rng(seed)
    frac = max_frames / total
    out = []
    for t in trajs:
        n = max(1, int(round(t.shape[0] * frac)))
        idx = np.sort(rng.choice(t.shape[0], n, replace=False))
        out.append(t[idx])
    print(f"Subsampled {total:,} -> {sum(t.shape[0] for t in out):,} frames for TICA fitting")
    return out


def fit_tica(feat_trajs: list[np.ndarray], lagtime: int, dim: int):
    model = TICA(lagtime=lagtime, dim=dim).fit(feat_trajs).fetch_model()
    return model


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def fes_from_coords(coords: np.ndarray, bins: int):
    h, xe, ye = np.histogram2d(coords[:, 0], coords[:, 1], bins=bins, density=True)
    h = np.maximum(h, 1e-10)
    F = -np.log(h)
    F -= F.min()
    xc = 0.5 * (xe[:-1] + xe[1:])
    yc = 0.5 * (ye[:-1] + ye[1:])
    return F, xc, yc


def plot_fes(coords: np.ndarray, bins: int, lagtime: int, protein: str, outpath: str):
    F, xc, yc = fes_from_coords(coords, bins)
    fig, ax = plt.subplots(figsize=(6, 5))
    cf = ax.contourf(xc, yc, F.T, levels=20, cmap="RdYlBu_r")
    ax.set_xlabel("TIC 1", fontsize=12)
    ax.set_ylabel("TIC 2", fontsize=12)
    ax.set_title(f"{protein} — TICA Free Energy Surface (lag={lagtime})", fontsize=12, fontweight="bold")
    plt.colorbar(cf, ax=ax, label="Free energy (kT)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def plot_implied_timescales(feat_trajs: list[np.ndarray], lags: list[int], dim: int, protein: str, outpath: str):
    timescales = []
    for lag in lags:
        try:
            m = TICA(lagtime=lag, dim=dim).fit(feat_trajs).fetch_model()
            timescales.append(m.timescales(lagtime=lag)[:dim])
        except Exception as e:
            print(f"  lag={lag} failed: {e}")
            timescales.append([np.nan] * dim)

    timescales = np.array(timescales)
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = plt.cm.tab10(np.linspace(0, 0.5, dim))
    for i in range(dim):
        ax.plot(lags, timescales[:, i], "o-", color=colors[i], label=f"TIC {i + 1}")
    ax.plot(lags, lags, "k--", lw=1, label="lag time (diagonal)")
    ax.set_xlabel("Lag time (frames)", fontsize=12)
    ax.set_ylabel("Implied timescale (frames)", fontsize=12)
    ax.set_title(f"{protein} — Implied Timescales", fontsize=12)
    ax.legend()
    ax.set_yscale("log")
    ax.set_xscale("log")
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--protein",    required=True,          help="Protein name, e.g. 1d3y_B")
    p.add_argument("--data-dir",   default="data",         help="Root data directory (default: data)")
    p.add_argument("--replicates", default="1,2,3",        help="Comma-separated replicate indices (default: 1,2,3)")
    p.add_argument("--lagtime",    type=int, default=10,   help="TICA lag time in frames (default: 10)")
    p.add_argument("--dim",        type=int, default=2,    help="Number of TIC components (default: 2)")
    p.add_argument("--subsample",  type=int, default=500_000, help="Max frames for TICA fitting (default: 500000)")
    p.add_argument("--bins",       type=int, default=100,  help="Histogram bins for FES plot (default: 100)")
    p.add_argument("--its-lags",   default="1,2,5,10,20,50,100,150,200",
                   help="Lag times for implied-timescales scan (default: 1,2,5,10,20,50,100,150,200)")
    p.add_argument("--out-dir",    default=None,
                   help="Output directory (default: analysis/<protein>)")
    p.add_argument("--skip-its",   action="store_true",    help="Skip implied-timescales scan")
    return p.parse_args()


def main():
    args = parse_args()

    out_dir = args.out_dir or os.path.join("analysis", args.protein)
    os.makedirs(out_dir, exist_ok=True)

    replicates = [int(r) for r in args.replicates.split(",")]

    # --- load ---
    print(f"\n=== {args.protein} ===")
    trajs = load_atlas_replicates(args.protein, args.data_dir, replicates)

    # --- featurize ---
    print("\nComputing phi/psi torsions …")
    phi_psi_list = compute_phi_psi(trajs)
    total_frames = sum(t.shape[0] for t in phi_psi_list)
    print(f"Total frames after filtering: {total_frames:,}")

    phi_psi_arr = np.array(phi_psi_list, dtype=object)
    phi_psi_path = os.path.join(out_dir, "phi_psi.npy")
    np.save(phi_psi_path, phi_psi_arr, allow_pickle=True)
    print(f"Saved: {phi_psi_path}")

    # --- TICA ---
    feat_trajs = [to_sincos(t) for t in phi_psi_list]
    fit_trajs  = subsample_trajs(feat_trajs, args.subsample)

    print(f"\nFitting TICA (lag={args.lagtime}, dim={args.dim}) …")
    model = fit_tica(fit_trajs, args.lagtime, args.dim)

    tic_per_traj = [model.transform(f) for f in feat_trajs]
    tic_all = np.concatenate(tic_per_traj, axis=0)
    print(f"TIC coordinates shape: {tic_all.shape}")

    # --- save arrays ---
    coords_path = os.path.join(out_dir, "tica_coords.npy")
    np.save(coords_path, tic_all)
    print(f"Saved: {coords_path}")

    per_traj_path = os.path.join(out_dir, "tica_coords_per_traj.npy")
    np.save(per_traj_path, np.array(tic_per_traj, dtype=object), allow_pickle=True)
    print(f"Saved: {per_traj_path}")

    model_path = os.path.join(out_dir, "tica_model.npz")
    np.savez(model_path,
             singular_vectors_left=model.singular_vectors_left,
             singular_values=model.singular_values,
             mean_0=model.mean_0,
             lagtime=args.lagtime,
             dim=args.dim)
    print(f"Saved: {model_path}")

    # --- plots ---
    plot_fes(tic_all, args.bins, args.lagtime, args.protein,
             os.path.join(out_dir, "tica_fes.png"))

    if not args.skip_its:
        its_lags = [int(x) for x in args.its_lags.split(",")]
        print("\nComputing implied timescales …")
        plot_implied_timescales(feat_trajs, its_lags, args.dim, args.protein,
                                os.path.join(out_dir, "tica_implied_timescales.png"))

    # --- summary ---
    print("\n-- TIC 1 statistics --")
    print(f"  mean={tic_all[:,0].mean():.3f}  std={tic_all[:,0].std():.3f}"
          f"  min={tic_all[:,0].min():.3f}  max={tic_all[:,0].max():.3f}")
    print("\nDone.")


if __name__ == "__main__":
    main()
