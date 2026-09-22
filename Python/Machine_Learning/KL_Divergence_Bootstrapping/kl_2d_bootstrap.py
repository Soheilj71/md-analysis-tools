# Purpose: Compare two 2D datasets (e.g., real vs synthetic) using KL divergence + bootstrap CI.  

import argparse  #  users run this script from the terminal with options like --real and --synth.
import csv  #  writing results into a CSV file (spreadsheet-friendly).
import math  # Provides math utilities (like log).
import sys  # Provides access to system functions (like exit).
from pathlib import Path  # Provides safe, cross-platform file paths.

import numpy as np  # Provides fast array math (needed for histograms, resampling).

# We import matplotlib only if the user asks for plotting.  
# This avoids failing if matplotlib is not installed.
# (If matplotlib is missing and user requests --plot, a clear message is shown.)
try:  # Start a safe "try" block.
    import matplotlib.pyplot as plt  # Plotting library (optional).
except Exception:  # If matplotlib is not available, it should be handled gracefully.
    plt = None  # "None" is stored so we can check later if plotting is possible.


def fail(message: str, code: int = 1) -> None:  # Define a helper function to stop with an error message.
    print(f"[ERROR] {message}", file=sys.stderr)  # Print the message to the error output (so it’s clearly an error).
    sys.exit(code)  # Exit the script with a non-zero code to signal failure.


def load_points_from_npy(npy_path: Path) -> np.ndarray:  # Define a function to load a .npy file into a 2D point list.
    if not npy_path.exists():  # Check that the file actually exists.
        fail(f"File not found: {npy_path}")  # If not, stop and explain clearly.

    arr = np.load(str(npy_path))  # Load the numpy array from disk.

    # We want points shaped (N, 2): each row is one point (x,y).  # Explaining the expected format.
    # But many MD datasets are (n_traj, n_steps, 2).  # We support that too.
    if arr.ndim == 2 and arr.shape[1] == 2:  # If it already looks like (N,2)...
        points = arr  # ...use it directly.
    elif arr.ndim == 3 and arr.shape[-1] == 2:  # If it looks like (n_traj, n_steps, 2)...
        points = arr.reshape(-1, 2)  # ...flatten it into (N,2) by merging traj and time dimensions.
    else:  # Otherwise the shape is not recognized.
        fail(
            f"{npy_path} has shape {arr.shape}, but expected (N,2) or (n_traj,n_steps,2)."
        )  # Explain what shapes are allowed.

    # Convert to float for safety (some arrays might be int).  # This avoids issues in probability computations.
    points = np.asarray(points, dtype=float)  # Ensure float type.

    # Remove rows with NaN or inf (bad numeric values).  # This is important for stable histogram math.
    mask_good = np.isfinite(points).all(axis=1)  # True for rows where both x and y are finite.
    points = points[mask_good]  # Keep only good rows.

    if points.shape[0] < 10:  # If too few points remain, KL becomes meaningless.
        fail(f"Too few valid points after cleaning in {npy_path} (got {points.shape[0]} points).")

    return points  # Return cleaned points shaped (N,2).


def choose_range(real_pts: np.ndarray, synth_pts: np.ndarray, pad_frac: float = 0.05) -> tuple:  # Define plot/hist range.
    # We combine both datasets to choose a shared histogram range.  # This makes KL comparison fair.
    all_pts = np.vstack([real_pts, synth_pts])  # Stack points (N_total,2).

    xmin = float(np.min(all_pts[:, 0]))  # Minimum x value.
    xmax = float(np.max(all_pts[:, 0]))  # Maximum x value.
    ymin = float(np.min(all_pts[:, 1]))  # Minimum y value.
    ymax = float(np.max(all_pts[:, 1]))  # Maximum y value.

    # Add padding so points on the edges are not cut off by histogram bins.  # Improves stability.
    xpad = (xmax - xmin) * pad_frac if xmax > xmin else 1.0  # Avoid zero width.
    ypad = (ymax - ymin) * pad_frac if ymax > ymin else 1.0  # Avoid zero height.

    return (xmin - xpad, xmax + xpad, ymin - ypad, ymax + ypad)  # Return (xmin,xmax,ymin,ymax).


def hist2d_prob(points: np.ndarray, bins: int, rng: tuple, eps: float) -> np.ndarray:  # Convert points into 2D probability grid.
    # Compute a 2D histogram (counts per bin).  # This discretizes the 2D distribution.
    counts, _, _ = np.histogram2d(  # histogram2d returns counts and bin edges.
        points[:, 0],  # x-values.
        points[:, 1],  # y-values.
        bins=bins,  # number of bins in each dimension.
        range=[[rng[0], rng[1]], [rng[2], rng[3]]],  # histogram range.
        density=False,  # We want raw counts first.
    )

    # Add a small epsilon to avoid zeros.  # KL requires log(P/Q); if Q=0 anywhere P>0 → infinite.
    counts = counts + eps  # Smooth counts by a tiny amount everywhere.

    # Convert counts to probabilities so they sum to 1.  # Probability grid P(i,j).
    prob = counts / np.sum(counts)  # Normalize.

    return prob  # Return probability grid.


def kl_divergence_discrete(P: np.ndarray, Q: np.ndarray) -> float:  # Compute KL(P || Q) for discrete grids.
    # KL(P||Q) = sum_{i} P_i * log(P_i / Q_i)  # Definition in discrete form.
    # Here i corresponds to (bin_x, bin_y).  # Explanation.

    # Flatten both grids into 1D vectors.  # Makes summation simpler.
    p = P.ravel()  # Flatten.
    q = Q.ravel()  # Flatten.

    # Safety checks.  # Better errors than silent wrong math.
    if p.shape != q.shape:  # Ensure same length.
        fail("Internal error: P and Q shapes differ in KL computation.")

    # Compute KL using numpy and math.log.  # We rely on numpy vectorization for speed.
    # Note: p and q should be strictly positive because of eps smoothing.  # Prevents log(0).
    kl = float(np.sum(p * np.log(p / q)))  # KL divergence in natural units (nats).

    return kl  # Return scalar KL value.


def bootstrap_kl(
    real_pts: np.ndarray,
    synth_pts: np.ndarray,
    bins: int,
    rng: tuple,
    eps: float,
    n_boot: int,
    seed: int,
) -> np.ndarray:  # Compute many bootstrap KL values.
    rng_np = np.random.default_rng(seed)  # Create a reproducible random generator.

    n_real = real_pts.shape[0]  # Number of real points.
    n_synth = synth_pts.shape[0]  # Number of synthetic points.

    # We store all bootstrap KL results here.  # This will be an array of length n_boot.
    kl_values = np.empty(n_boot, dtype=float)  # Pre-allocate for speed.

    for b in range(n_boot):  # Loop over bootstrap repetitions.
        # Sample with replacement from the real points.  # Standard bootstrap idea.
        idx_r = rng_np.integers(0, n_real, size=n_real)  # Random indices of same size as original.
        boot_real = real_pts[idx_r]  # Bootstrapped real sample.

        # Sample with replacement from the synthetic points.  # Also bootstrap the synthetic distribution.
        idx_s = rng_np.integers(0, n_synth, size=n_synth)  # Random indices.
        boot_synth = synth_pts[idx_s]  # Bootstrapped synthetic sample.

        # Convert each bootstrapped sample into a probability grid.  # Now we can compute KL on grids.
        P = hist2d_prob(boot_real, bins=bins, rng=rng, eps=eps)  # P = probability of real.
        Q = hist2d_prob(boot_synth, bins=bins, rng=rng, eps=eps)  # Q = probability of synth.

        # Compute KL(P||Q).  # How different real is from synth.
        kl_values[b] = kl_divergence_discrete(P, Q)  # Store the result.

    return kl_values  # Return array of bootstrap KL values.


def percentile_ci(values: np.ndarray, alpha: float = 0.05) -> tuple:  # Compute a percentile confidence interval.
    lo = float(np.percentile(values, 100.0 * (alpha / 2.0)))  # Lower bound (e.g., 2.5% for alpha=0.05).
    hi = float(np.percentile(values, 100.0 * (1.0 - alpha / 2.0)))  # Upper bound (e.g., 97.5%).
    return (lo, hi)  # Return (lower, upper).


def write_csv(out_csv: Path, row: dict) -> None:  # Save a single-row CSV with results.
    out_csv.parent.mkdir(parents=True, exist_ok=True)  # Create folders if they do not exist.

    # Define a stable column order.  # Makes CSV consistent across runs.
    fieldnames = list(row.keys())  # Use the dictionary keys as columns.

    with out_csv.open("w", newline="", encoding="utf-8") as f:  # Open output file.
        writer = csv.DictWriter(f, fieldnames=fieldnames)  # Create CSV writer.
        writer.writeheader()  # Write the header row (column names).
        writer.writerow(row)  # Write one row of data.


def maybe_plot(real_pts: np.ndarray, synth_pts: np.ndarray, rng: tuple, out_png: Path) -> None:  # Make a simple scatter plot.
    if plt is None:  # If matplotlib could not be imported...
        fail("Plot requested but matplotlib is not installed. Install it or remove --plot.")  # Explain how to fix.

    out_png.parent.mkdir(parents=True, exist_ok=True)  # Ensure output folder exists.

    fig = plt.figure()  # Create a new figure.
    ax = fig.add_subplot(1, 1, 1)  # Create one axis.

    ax.scatter(real_pts[:, 0], real_pts[:, 1], s=2, alpha=0.4, label="Real")  # Plot real points.
    ax.scatter(synth_pts[:, 0], synth_pts[:, 1], s=2, alpha=0.4, label="Synthetic")  # Plot synthetic points.

    ax.set_xlim(rng[0], rng[1])  # Set x range.
    ax.set_ylim(rng[2], rng[3])  # Set y range.
    ax.set_xlabel("x")  # Label x axis.
    ax.set_ylabel("y")  # Label y axis.
    ax.set_title("Real vs Synthetic points (quick visual check)")  # Title.
    ax.legend()  # Show legend.

    fig.tight_layout()  # Reduce whitespace around the plot.
    fig.savefig(str(out_png), dpi=200)  # Save the plot to a file.
    plt.close(fig)  # Close the figure to free memory.


def main() -> None:  # Main function: this is where the script starts doing the work.
    parser = argparse.ArgumentParser(  # Create a command-line parser.
        description="Compute KL divergence KL(P_real || P_synth) in 2D using histograms, with bootstrap CI."
    )  # Add a short description.

    parser.add_argument("--real", required=True, help="Path to real samples .npy (shape (N,2) or (n_traj,n_steps,2)).")
    parser.add_argument("--synth", required=True, help="Path to synthetic samples .npy (shape (N,2) or (n_traj,n_steps,2)).")

    parser.add_argument("--bins", type=int, default=60, help="Number of histogram bins per dimension (default: 60).")
    parser.add_argument("--eps", type=float, default=1e-12, help="Small smoothing value added to every bin (default: 1e-12).")

    parser.add_argument("--n_boot", type=int, default=200, help="Number of bootstrap samples (default: 200).")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for reproducibility (default: 0).")

    parser.add_argument("--out_csv", default="", help="Optional path to write a one-row CSV summary.")
    parser.add_argument("--plot", default="", help="Optional path to save a quick scatter plot PNG.")

    args = parser.parse_args()  # Parse arguments provided by the user.

    real_path = Path(args.real)  # Convert real file path to Path.
    synth_path = Path(args.synth)  # Convert synth file path to Path.

    real_pts = load_points_from_npy(real_path)  # Load and clean real points.
    synth_pts = load_points_from_npy(synth_path)  # Load and clean synthetic points.

    rng = choose_range(real_pts, synth_pts, pad_frac=0.05)  # Choose a shared histogram range.

    P = hist2d_prob(real_pts, bins=args.bins, rng=rng, eps=args.eps)  # Compute probability grid for real.
    Q = hist2d_prob(synth_pts, bins=args.bins, rng=rng, eps=args.eps)  # Compute probability grid for synthetic.

    kl_point = kl_divergence_discrete(P, Q)  # Compute KL on full data (one estimate).

    kl_boot = bootstrap_kl(  # Compute bootstrap distribution of KL values.
        real_pts=real_pts,
        synth_pts=synth_pts,
        bins=args.bins,
        rng=rng,
        eps=args.eps,
        n_boot=args.n_boot,
        seed=args.seed,
    )

    ci_lo, ci_hi = percentile_ci(kl_boot, alpha=0.05)  # Compute 95% bootstrap CI (percentile method).

    print("KL divergence (nats):")  # Print a label.
    print(f"  KL(P_real || P_synth) = {kl_point:.6g}")  # Print point estimate.
    print("Bootstrap 95% CI (percentile):")  # Print CI label.
    print(f"  [{ci_lo:.6g}, {ci_hi:.6g}]")  # Print CI bounds.

    # Optionally write CSV output.  # This is helpful for Excel or storing results in sweeps.
    if args.out_csv.strip():  # If user provided a non-empty path...
        out_csv = Path(args.out_csv)  # Convert to Path.
        row = {  # Create a summary row.
            "real_file": str(real_path),  # Record input.
            "synth_file": str(synth_path),  # Record input.
            "bins": int(args.bins),  # Record bins.
            "eps": float(args.eps),  # Record eps.
            "n_boot": int(args.n_boot),  # Record bootstrap count.
            "seed": int(args.seed),  # Record seed.
            "kl_point_nats": float(kl_point),  # Record point estimate.
            "ci95_lo_nats": float(ci_lo),  # Record CI lower.
            "ci95_hi_nats": float(ci_hi),  # Record CI upper.
        }
        write_csv(out_csv, row)  # Write CSV.
        print(f"Wrote CSV: {out_csv}")  # Confirm.

    # Optionally generate a plot.  # Good for sanity-checking distributions.
    if args.plot.strip():  # If user provided a plot path...
        out_png = Path(args.plot)  # Convert to Path.
        maybe_plot(real_pts, synth_pts, rng=rng, out_png=out_png)  # Create plot.
        print(f"Wrote plot: {out_png}")  # Confirm.


if __name__ == "__main__":  # This line ensures main() runs only when you execute this file directly.
    main()  # Call the main function.
