#!/usr/bin/env python3
"""
bootstrap.py -- bootstrap confidence intervals for a statistic of sampled data.

For each input file it:

  1. loads the samples (.npy / .npz / .txt / .csv),
  2. draws B bootstrap replicates, resampling either individual frames or
     whole trajectories with replacement,
  3. evaluates a statistic on every replicate, and
  4. reports the statistic on the original data plus the bootstrap mean,
     percentile confidence interval and standard deviation.

Built-in statistics (histogram based, need a --reference):
    kl   KL(sample || reference)
    js   Jensen-Shannon divergence between sample and reference

Any other statistic can be plugged in with --stat FILE.py:FUNC or
--stat package.module:FUNC, where FUNC(x) takes an (N, d) float array and
returns a float.

References for kl / js:
    muller   analytic Mueller-Brown Boltzmann distribution (2-D benchmark)
    grid     probabilities on a regular grid stored in an .npz (axis arrays
             named by --grid-keys, probabilities by --weights-key); the grid
             also defines the histogram bins
    samples  histogram of reference samples (.npy, or .npz with --ref-key)

Examples
--------
Any statistic of your own, one CI per file:

    python bootstrap.py --input 'runs/*.npy' --stat my_stats.py:mean_energy

KL divergence of 2-D samples from reference samples, two conditions:

    python bootstrap.py \\
        --input modelA='results/modelA/*.npy' \\
        --input modelB='results/modelB/*.npy' \\
        --reference samples --ref-file reference.npy \\
        --range -3 3 -3 3 --bins 100 --out results/kl

Correlated data stored as (n_traj, n_steps, d): resample whole trajectories:

    python bootstrap.py --input 'sims/*.npy' --resample trajectories \\
        --reference muller --range -1.5 1.2 -0.5 2.0 --bins 150

Parameters parsed from file names (e.g. run_T300_N64.npy), filtered and
arranged into heatmaps:

    python bootstrap.py --input 'runs/run_*.npy' \\
        --label-regex 'T(?P<T>\\d+)_N(?P<N>\\d+)' --where 'T >= 300' --pivot T N \\
        --reference grid --ref-file ref_grid.npz --grid-keys x_grid y_grid

Settings can also be kept in a JSON file whose keys are the long option
names (dashes or underscores), e.g. --config examples/config.json.
Command-line flags override the config file.
"""
from __future__ import annotations

import argparse
import csv
import glob
import importlib
import importlib.util
import json
import os
import platform
import re
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np

HIST_STATS = ("kl", "js")


# -- Loading -----------------------------------------------------------------

def load_array(path: str | Path, key: str | None = None) -> np.ndarray:
    """Load a numeric array from .npy, .npz (optionally by key), .csv or text."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".npy":
        arr = np.load(path)
    elif suffix == ".npz":
        with np.load(path) as z:
            if key is None:
                if len(z.files) != 1:
                    raise ValueError(f"{path} holds {z.files}; choose one with --key")
                key = z.files[0]
            arr = z[key]
    elif suffix == ".csv":
        arr = np.loadtxt(path, delimiter=",", comments="#", ndmin=2)
    else:
        arr = np.loadtxt(path, comments="#", ndmin=2)
    return np.asarray(arr, dtype=np.float64)


def as_frames(arr: np.ndarray, columns: list[int] | None) -> np.ndarray:
    """Any array whose last axis is the coordinate axis -> (N, d)."""
    if arr.ndim == 1:
        arr = arr[:, None]
    x = arr.reshape(-1, arr.shape[-1])
    return x[:, columns] if columns else x


def as_trajectories(arr: np.ndarray, columns: list[int] | None) -> np.ndarray:
    """(n_traj, n_steps, ..., d) -> (n_traj, n_frames_per_traj, d)."""
    if arr.ndim < 3:
        raise ValueError(
            f"--resample trajectories needs an array shaped (n_traj, n_steps, ..., d); "
            f"got {arr.shape}")
    x = arr.reshape(arr.shape[0], -1, arr.shape[-1])
    return x[..., columns] if columns else x


def load_callable(spec: str):
    """'path/to/file.py:func' or 'package.module:func' -> the function."""
    module_part, sep, func_name = spec.rpartition(":")
    if not sep:
        raise ValueError(f"--stat must be 'kl', 'js' or MODULE:FUNC, got {spec!r}")
    if module_part.endswith(".py"):
        mod_spec = importlib.util.spec_from_file_location(Path(module_part).stem, module_part)
        module = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(module)
    else:
        module = importlib.import_module(module_part)
    return getattr(module, func_name)


# -- Histogram grid and reference distributions ------------------------------

class Grid:
    """Rectangular d-dimensional histogram grid with an extra overflow bin.

    Bin semantics match numpy.histogramdd: bins are half-open [a, b) except the
    last one along each axis, which is closed. Points outside the window (or NaN)
    go to the overflow bin, index n_bins.
    """

    def __init__(self, edges: list[np.ndarray]):
        self.edges = [np.asarray(e, dtype=np.float64) for e in edges]
        self.shape = tuple(len(e) - 1 for e in self.edges)
        self.n_bins = int(np.prod(self.shape))

    @property
    def dim(self) -> int:
        return len(self.edges)

    def bin_index(self, x: np.ndarray) -> np.ndarray:
        if x.shape[1] != self.dim:
            raise ValueError(f"data has {x.shape[1]} columns but the grid is {self.dim}-D; "
                             f"select columns with --columns")
        flat = np.zeros(len(x), dtype=np.int64)
        inside = np.ones(len(x), dtype=bool)
        for k, e in enumerate(self.edges):
            col = x[:, k]
            inside &= (col >= e[0]) & (col <= e[-1])
            i = np.clip(np.searchsorted(e, col, side="right") - 1, 0, len(e) - 2)
            flat = flat * (len(e) - 1) + i
        flat[~inside] = self.n_bins
        return flat

    def counts(self, bin_idx: np.ndarray) -> np.ndarray:
        return np.bincount(bin_idx, minlength=self.n_bins + 1)


def grid_from_range(ranges: list[float], bins: list[int]) -> Grid:
    if len(ranges) % 2:
        raise ValueError("--range needs pairs: MIN MAX [MIN MAX ...]")
    dim = len(ranges) // 2
    if len(bins) == 1:
        bins = bins * dim
    if len(bins) != dim:
        raise ValueError(f"--bins needs 1 or {dim} values, got {len(bins)}")
    return Grid([np.linspace(ranges[2 * k], ranges[2 * k + 1], bins[k] + 1)
                 for k in range(dim)])


def muller_potential(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    aa = np.array([-1.0, -1.0, -6.5, 0.7])
    bb = np.array([0.0, 0.0, 11.0, 0.6])
    cc = np.array([-10.0, -10.0, -6.5, 0.7])
    AA = np.array([-200.0, -100.0, -170.0, 15.0])
    XX = np.array([1.0, 0.0, -0.5, -1.0])
    YY = np.array([0.0, 0.5, 1.5, 1.0])
    V = np.zeros_like(x, dtype=np.float64)
    for j in range(4):
        arg = (aa[j] * (x - XX[j]) ** 2
               + bb[j] * (x - XX[j]) * (y - YY[j])
               + cc[j] * (y - YY[j]) ** 2)
        V += AA[j] * np.exp(np.clip(arg, -700.0, 700.0))
    return np.nan_to_num(V, posinf=1e308, neginf=-1e308, nan=0.0)


def muller_bin_mass(grid: Grid, beta: float, grid_steps: int) -> np.ndarray:
    """Boltzmann weight exp(-beta (V - Vmin)) on a fine grid, summed into bins."""
    if grid.dim != 2:
        raise ValueError("--reference muller needs a 2-D grid")
    xe, ye = grid.edges
    xx, yy = np.meshgrid(np.linspace(xe[0], xe[-1], grid_steps),
                         np.linspace(ye[0], ye[-1], grid_steps), indexing="xy")
    V = muller_potential(xx, yy)
    W = np.exp(np.clip(-beta * (V - np.nanmin(V)), -700.0, 700.0))
    H, _, _ = np.histogram2d(xx.ravel(), yy.ravel(), bins=[xe, ye], weights=W.ravel())
    if not np.isfinite(H.sum()) or H.sum() <= 0.0:
        H = np.ones_like(H)
    return H


def grid_file_mass(path: str, grid_keys: list[str], weights_key: str) -> tuple[Grid, np.ndarray]:
    """Reference probabilities stored on a regular grid in an .npz.

    Axis values are taken as left bin edges of a uniform grid (e.g. -180, -175,
    ..., 175); the last edge is one step past the last value. Axis arrays may be
    1-D or meshgrid-style ('ij' indexing).
    """
    with np.load(path) as z:
        grids = [np.asarray(z[k], dtype=np.float64) for k in grid_keys]
        weights = np.asarray(z[weights_key], dtype=np.float64)
    dim = len(grids)
    edges = []
    for k, g in enumerate(grids):
        vals = g[tuple(slice(None) if a == k else 0 for a in range(dim))] if g.ndim == dim else g
        step = float(vals[1] - vals[0])
        edges.append(np.append(vals, vals[-1] + step))
    grid = Grid(edges)
    return grid, weights.reshape(grid.shape)


def build_reference(args) -> tuple[Grid, np.ndarray]:
    """Return (grid, q) with q the reference probability per bin (+ overflow)."""
    if args.reference == "grid":
        grid, mass = grid_file_mass(args.ref_file, args.grid_keys, args.weights_key)
    else:
        if not args.range:
            raise ValueError(f"--reference {args.reference} needs --range")
        grid = grid_from_range(args.range, args.bins)
        if args.reference == "muller":
            mass = muller_bin_mass(grid, args.beta, args.grid_steps)
        elif args.reference == "samples":
            ref = as_frames(load_array(args.ref_file, args.ref_key), args.columns)
            mass = grid.counts(grid.bin_index(ref))[:-1].astype(np.float64)
        else:
            raise ValueError(f"unknown --reference {args.reference!r}")

    ref_eps = args.eps if args.ref_eps is None else args.ref_eps
    q = np.asarray(mass, dtype=np.float64).ravel()
    q = np.clip(q / q.sum(), ref_eps, 1.0)
    q /= q.sum()
    if args.overflow:
        # probability of leaving the window under the reference is ~0
        q = np.append(q, ref_eps)
        q /= q.sum()
    return grid, q


# -- Statistics --------------------------------------------------------------

def counts_to_prob(counts: np.ndarray, eps: float, overflow: bool) -> np.ndarray:
    c = np.asarray(counts if overflow else counts[:-1], dtype=np.float64)
    total = c.sum()
    p = c / total if total > 0 else np.full_like(c, 1.0 / c.size)
    p = np.clip(p, eps, 1.0)
    return p / p.sum()


def kl_from_counts(counts, q, log_q, eps, overflow) -> float:
    p = counts_to_prob(counts, eps, overflow)
    return float(np.sum(p * (np.log(p) - log_q)))


def js_from_counts(counts, q, log_q, eps, overflow) -> float:
    p = counts_to_prob(counts, eps, overflow)
    m = 0.5 * (p + q)
    log_m = np.log(m)
    return float(0.5 * np.sum(p * (np.log(p) - log_m)) + 0.5 * np.sum(q * (log_q - log_m)))


HIST_FUNCS = {"kl": kl_from_counts, "js": js_from_counts}


# -- Bootstrap worker --------------------------------------------------------

def file_seed(seed: int, condition: str, path: str) -> np.random.SeedSequence:
    """Per-file seed: reproducible no matter which other files are in the run."""
    return np.random.SeedSequence([seed, zlib.crc32(f"{condition}/{Path(path).name}".encode())])


def bootstrap_file(task: dict) -> dict:
    cfg = task["cfg"]
    path, condition = task["path"], task["condition"]
    rng = np.random.default_rng(file_seed(cfg["seed"], condition, path))
    B = cfg["n_boot"]
    arr = load_array(path, cfg["key"])
    trajectories = cfg["resample"] == "trajectories"
    info = {"n_traj": "", "n_per_replicate": ""}

    if cfg["stat"] in HIST_STATS:
        grid = Grid(task["edges"])
        q = task["q"]
        log_q = np.log(q)
        f = HIST_FUNCS[cfg["stat"]]
        eps, overflow = cfg["eps"], cfg["overflow"]
        stat = lambda counts: f(counts, q, log_q, eps, overflow)

        if trajectories:
            x = as_trajectories(arr, cfg["columns"])
            M, T, d = x.shape
            bins = grid.bin_index(x.reshape(-1, d)).reshape(M, T)
            n_pick = cfg["n_per_replicate"] or M
            n_points = M * T
            original = stat(grid.counts(bins.ravel()))
            reps = np.array([stat(grid.counts(bins[rng.integers(0, M, n_pick)].ravel()))
                             for _ in range(B)])
            info = {"n_traj": M, "n_per_replicate": n_pick}
        else:
            bins = grid.bin_index(as_frames(arr, cfg["columns"]))
            n_points = len(bins)
            counts0 = grid.counts(bins)
            original = stat(counts0)
            # Histogramming n points drawn with replacement gives bin counts that
            # are exactly Multinomial(n, counts0 / n) -- same distribution, O(bins).
            p0 = counts0 / n_points
            reps = np.array([stat(rng.multinomial(n_points, p0)) for _ in range(B)])
        out_of_window = int((bins == grid.n_bins).sum())
    else:
        func = load_callable(cfg["stat"])
        out_of_window = ""
        if trajectories:
            x = as_trajectories(arr, cfg["columns"])
            M, T, d = x.shape
            n_pick = cfg["n_per_replicate"] or M
            n_points = M * T
            original = float(func(x.reshape(-1, d)))
            reps = np.array([float(func(x[rng.integers(0, M, n_pick)].reshape(-1, d)))
                             for _ in range(B)])
            info = {"n_traj": M, "n_per_replicate": n_pick}
        else:
            x = as_frames(arr, cfg["columns"])
            n_points = len(x)
            original = float(func(x))
            reps = np.array([float(func(x[rng.integers(0, n_points, n_points)]))
                             for _ in range(B)])

    alpha = (100.0 - cfg["ci"]) / 2.0
    lo, hi = np.percentile(reps, [alpha, 100.0 - alpha])
    name, ci = cfg["name"], f"{cfg['ci']:g}"
    row = {
        "condition": condition,
        "file": path,
        **task["labels"],
        "n_points": n_points,
        **info,
        "out_of_window": out_of_window,
        f"{name}_orig": original,
        f"{name}_mean": float(np.mean(reps)),
        f"{name}_lo{ci}": float(lo),
        f"{name}_hi{ci}": float(hi),
        f"{name}_std": float(np.std(reps, ddof=1)),
        "CI_width": float(hi - lo),
    }
    if cfg["save_replicates"]:
        row["_replicates"] = reps
    return row


# -- Input discovery ---------------------------------------------------------

def parse_inputs(specs: list[str]) -> dict[str, list[str]]:
    """'NAME=GLOB' or 'GLOB' (condition 'all'); repeated names are merged."""
    conditions: dict[str, list[str]] = {}
    for spec in specs:
        name, sep, pattern = spec.partition("=")
        if not sep or not re.fullmatch(r"[\w.%+-]+", name):
            name, pattern = "all", spec
        conditions.setdefault(name, []).append(pattern)
    return conditions


def cast(value: str):
    for t in (int, float):
        try:
            return t(value)
        except ValueError:
            pass
    return value


def discover(conditions: dict[str, list[str]], label_regex: str, where: str | None):
    regex = re.compile(label_regex) if label_regex else None
    found, skipped = [], []
    for condition, patterns in conditions.items():
        paths = sorted({p for pat in patterns for p in glob.glob(pat, recursive=True)
                        if os.path.isfile(p)})
        for path in paths:
            m = regex.search(Path(path).name) if regex else None
            labels = {k: cast(v) for k, v in m.groupdict().items()} if m else {}
            if where:
                try:
                    keep = eval(where, {"__builtins__": {}}, dict(labels))
                except Exception as exc:
                    skipped.append((path, f"--where failed: {exc}"))
                    continue
                if not keep:
                    continue
            found.append({"condition": condition, "path": path, "labels": labels})
    return found, skipped


# -- Output ------------------------------------------------------------------

def safe_name(name: str) -> str:
    return re.sub(r"[^\w.-]", "_", name.replace("%", "pct"))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def write_pivot(path: Path, rows: list[dict], row_key: str, col_key: str, value: str) -> None:
    rows_vals = sorted({r[row_key] for r in rows})
    cols_vals = sorted({r[col_key] for r in rows})
    lookup = {(r[row_key], r[col_key]): r[value] for r in rows}
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([f"{row_key}\\{col_key}"] + cols_vals)
        for rv in rows_vals:
            w.writerow([rv] + [lookup.get((rv, cv), "") for cv in cols_vals])


def plot_pivot(path: Path, rows: list[dict], row_key: str, col_key: str,
               value: str, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows_vals = sorted({r[row_key] for r in rows})
    cols_vals = sorted({r[col_key] for r in rows})
    lookup = {(r[row_key], r[col_key]): r[value] for r in rows}
    grid = np.array([[lookup.get((rv, cv), np.nan) for cv in cols_vals] for rv in rows_vals])
    fig, ax = plt.subplots(figsize=(max(6, 0.35 * len(cols_vals) + 3),
                                    max(4, 0.3 * len(rows_vals) + 2)))
    im = ax.imshow(grid, aspect="auto", origin="lower", cmap="viridis")
    ax.set_xticks(range(len(cols_vals)), [str(c) for c in cols_vals], rotation=90, fontsize=7)
    ax.set_yticks(range(len(rows_vals)), [str(r) for r in rows_vals], fontsize=7)
    ax.set_xlabel(col_key)
    ax.set_ylabel(row_key)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=value)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def best_summary(rows_by_cond: dict[str, list[dict]], cfg: dict, label_keys: list[str]) -> list[dict]:
    """Best vs runner-up per condition; 'robust' when their CIs do not overlap."""
    name, ci = cfg["name"], f"{cfg['ci']:g}"
    mean, lo, hi = f"{name}_mean", f"{name}_lo{ci}", f"{name}_hi{ci}"
    out = []
    for condition, rows in rows_by_cond.items():
        if len(rows) < 2:
            continue
        ranked = sorted(rows, key=lambda r: r[mean], reverse=cfg["best"] == "max")
        best, second = ranked[0], ranked[1]
        robust = best[hi] < second[lo] if cfg["best"] == "min" else best[lo] > second[hi]
        entry = {"condition": condition, "n_files": len(rows)}
        for tag, r in (("best", best), ("runner_up", second)):
            entry[f"{tag}_file"] = Path(r["file"]).name
            for k in label_keys:
                entry[f"{tag}_{k}"] = r.get(k, "")
            entry[f"{tag}_{mean}"] = r[mean]
            entry[f"{tag}_{lo}"] = r[lo]
            entry[f"{tag}_{hi}"] = r[hi]
        entry["robust"] = robust
        out.append(entry)
    return out


# -- CLI ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", type=Path, help="JSON file with default values for any option")

    g = p.add_argument_group("input")
    g.add_argument("--input", action="append", default=None, metavar="[NAME=]GLOB",
                   help="files to bootstrap; repeat for several conditions. '**' recurses.")
    g.add_argument("--key", help="array name inside .npz input files")
    g.add_argument("--columns", type=int, nargs="+",
                   help="coordinate columns (last axis) to use; default: all")
    g.add_argument("--label-regex",
                   help="regex with named groups, matched against each file name; the "
                        "groups become CSV columns, e.g. 'T(?P<T>\\d+)_N(?P<N>\\d+)'")
    g.add_argument("--where",
                   help="keep only files whose labels satisfy this expression, e.g. 'T >= 300 and N < 128'")

    g = p.add_argument_group("bootstrap")
    g.add_argument("--stat", default="kl",
                   help="'kl', 'js', or FILE.py:FUNC / module:FUNC taking an (N, d) array")
    g.add_argument("--name", help="column prefix for the statistic (default: KL, JS or FUNC)")
    g.add_argument("--resample", choices=["frames", "trajectories"], default="frames",
                   help="resampling unit (default: frames). 'trajectories' keeps the "
                        "time correlation inside each trajectory")
    g.add_argument("--n-per-replicate", type=int,
                   help="trajectories drawn per replicate (default: all)")
    g.add_argument("--n-boot", type=int, default=1000, help="replicates (default: 1000)")
    g.add_argument("--ci", type=float, default=95.0, help="CI level in %% (default: 95)")
    g.add_argument("--seed", type=int, default=42)
    g.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))

    g = p.add_argument_group("reference distribution (kl / js)")
    g.add_argument("--reference", choices=["muller", "grid", "samples"])
    g.add_argument("--ref-file", help="reference file for 'grid' / 'samples'")
    g.add_argument("--ref-key", help="array name in an .npz for 'samples'")
    g.add_argument("--grid-keys", nargs="+",
                   help="axis arrays in the 'grid' .npz, one per dimension")
    g.add_argument("--weights-key", default="weights",
                   help="probability array in the 'grid' .npz (default: weights)")
    g.add_argument("--range", type=float, nargs="+", metavar="MIN MAX",
                   help="histogram window, one MIN MAX pair per dimension")
    g.add_argument("--bins", type=int, nargs="+", default=[150],
                   help="bins per dimension, one value or one per dimension (default: 150)")
    g.add_argument("--beta", type=float, default=1.0, help="Mueller inverse temperature")
    g.add_argument("--grid-steps", type=int, default=300,
                   help="fine-grid points per axis for the Mueller reference (default: 300)")
    g.add_argument("--eps", type=float, default=1e-12,
                   help="probability floor for the sample histogram (default: 1e-12)")
    g.add_argument("--ref-eps", type=float,
                   help="probability floor for the reference (default: same as --eps)")
    g.add_argument("--no-overflow", dest="overflow", action="store_false",
                   help="drop points outside the window instead of counting them in an "
                        "extra overflow bin")

    g = p.add_argument_group("output")
    g.add_argument("--out", type=Path, default=Path("bootstrap_results"))
    g.add_argument("--pivot", nargs=2, metavar=("ROW", "COL"),
                   help="two labels (from --label-regex) to lay out as heatmap tables")
    g.add_argument("--best", choices=["min", "max", "none"], default="min",
                   help="rank files per condition and test best vs runner-up (default: min)")
    g.add_argument("--plot", action="store_true", help="save heatmap PNGs (needs matplotlib)")
    g.add_argument("--save-replicates", action="store_true",
                   help="save every replicate value to <out>/<condition>/replicates/*.npy")
    g.add_argument("--dry-run", action="store_true", help="list matched files and exit")
    return p


def parse_args(argv=None) -> argparse.Namespace:
    parser = build_parser()
    pre, _ = parser.parse_known_args(argv)
    if pre.config:
        with open(pre.config) as f:
            cfg = {k.replace("-", "_"): v for k, v in json.load(f).items()}
        if "no_overflow" in cfg:
            cfg["overflow"] = not cfg.pop("no_overflow")
        if isinstance(cfg.get("input"), dict):
            cfg["input"] = [f"{k}={v}" for k, vs in cfg["input"].items()
                            for v in (vs if isinstance(vs, list) else [vs])]
        known = {a.dest for a in parser._actions}
        unknown = set(cfg) - known
        if unknown:
            parser.error(f"unknown keys in {pre.config}: {sorted(unknown)}")
        parser.set_defaults(**cfg)
    args = parser.parse_args(argv)

    if not args.input:
        parser.error("no --input given")
    if args.stat in HIST_STATS and not args.reference:
        parser.error(f"--stat {args.stat} needs --reference")
    if args.reference in ("grid", "samples") and not args.ref_file:
        parser.error(f"--reference {args.reference} needs --ref-file")
    if args.reference == "grid" and not args.grid_keys:
        parser.error("--reference grid needs --grid-keys")
    if args.pivot and not args.label_regex:
        parser.error("--pivot needs --label-regex to define the labels")
    if args.name is None:
        args.name = args.stat.upper() if args.stat in HIST_STATS else args.stat.rpartition(":")[2]
    return args


def main(argv=None) -> None:
    args = parse_args(argv)
    conditions = parse_inputs(args.input)
    tasks, skipped = discover(conditions, args.label_regex, args.where)

    print(f"Matched {len(tasks)} files in {len(conditions)} condition(s)")
    for condition in conditions:
        n = sum(t["condition"] == condition for t in tasks)
        print(f"  {condition:<20s} {n:5d} files   {' '.join(conditions[condition])}")
    for path, why in skipped:
        print(f"  [skip] {path}: {why}")
    if args.dry_run:
        for t in tasks:
            print(f"  {t['condition']}  {t['path']}  {t['labels']}")
        return
    if not tasks:
        sys.exit("Nothing to do: no input files matched.")

    cfg = {k: getattr(args, k) for k in ("stat", "name", "resample", "n_per_replicate",
                                         "n_boot", "ci", "seed", "key", "columns",
                                         "eps", "overflow", "save_replicates", "best")}
    if args.stat in HIST_STATS:
        grid, q = build_reference(args)
        ref = {"edges": grid.edges, "q": q}
        shape = "x".join(map(str, grid.shape))
        print(f"Reference: {args.reference}  grid {shape}  "
              f"overflow bin {'on' if args.overflow else 'off'}  eps {args.eps:g}")
    else:
        load_callable(args.stat)  # fail fast on a bad spec
        ref = {}
    for t in tasks:
        t.update(cfg=cfg, **ref)

    print(f"Bootstrapping: stat={args.stat}  B={args.n_boot}  resample={args.resample}  "
          f"workers={args.workers}\n")
    t0 = time.time()
    rows, errors = [], []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(bootstrap_file, t): t for t in tasks}
        for i, fut in enumerate(as_completed(futures), 1):
            t = futures[fut]
            try:
                row = fut.result()
            except Exception as exc:
                errors.append((t["path"], repr(exc)))
                print(f"  [{i}/{len(tasks)}] ERROR {t['path']}: {exc}")
                continue
            rows.append(row)
            elapsed = time.time() - t0
            eta = elapsed / i * (len(tasks) - i)
            ci = f"{args.ci:g}"
            print(f"  [{i}/{len(tasks)}] {row['condition']}  {Path(row['file']).name}  "
                  f"{args.name}={row[f'{args.name}_mean']:.4f} "
                  f"[{row[f'{args.name}_lo{ci}']:.4f}, {row[f'{args.name}_hi{ci}']:.4f}]  "
                  f"({elapsed:.0f}s, ETA {eta:.0f}s)", flush=True)

    label_keys = list(dict.fromkeys(k for t in tasks for k in t["labels"]))
    rows.sort(key=lambda r: (r["condition"], *[str(r.get(k, "")).zfill(12) for k in label_keys],
                             r["file"]))
    ci = f"{args.ci:g}"
    stat_cols = [f"{args.name}_orig", f"{args.name}_mean", f"{args.name}_lo{ci}",
                 f"{args.name}_hi{ci}", f"{args.name}_std", "CI_width"]
    fields = (["condition", "file"] + label_keys
              + ["n_points", "n_traj", "n_per_replicate", "out_of_window"] + stat_cols)

    pivot = args.pivot
    args.out.mkdir(parents=True, exist_ok=True)
    by_cond: dict[str, list[dict]] = {}
    for r in rows:
        by_cond.setdefault(r["condition"], []).append(r)

    for condition, crow in by_cond.items():
        d = args.out / safe_name(condition)
        d.mkdir(parents=True, exist_ok=True)
        write_csv(d / "bootstrap_summary.csv", crow, [f for f in fields if f != "condition"])
        if pivot:
            for value, fname in [(f"{args.name}_mean", "heatmap_mean.csv"),
                                 (f"{args.name}_std", "heatmap_std.csv"),
                                 ("CI_width", "heatmap_ci_width.csv")]:
                write_pivot(d / fname, crow, *pivot, value)
            if args.plot:
                plot_pivot(d / "heatmap_mean.png", crow, *pivot, f"{args.name}_mean",
                           f"{condition}: bootstrap mean {args.name}")
                plot_pivot(d / "heatmap_ci_width.png", crow, *pivot, "CI_width",
                           f"{condition}: {ci}% CI width")
        if args.save_replicates:
            (d / "replicates").mkdir(exist_ok=True)
            for r in crow:
                np.save(d / "replicates" / f"{Path(r['file']).stem}.npy", r["_replicates"])

    write_csv(args.out / "bootstrap_all.csv", rows, fields)
    if args.best != "none":
        summary = best_summary(by_cond, cfg, label_keys)
        if summary:
            write_csv(args.out / "best_summary.csv", summary, list(summary[0]))
            print(f"\nBest per condition ({args.best} {args.name}_mean):")
            for s in summary:
                print(f"  {s['condition']:<20s} {s['best_file']}  "
                      f"robust (CI separated from runner-up): {s['robust']}")

    run_info = {
        "command": " ".join(sys.argv),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "n_files": len(rows),
        "errors": errors,
        "args": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
    }
    with open(args.out / "run_config.json", "w") as f:
        json.dump(run_info, f, indent=2)

    print(f"\nDone in {time.time() - t0:.0f}s: {len(rows)} files, {len(errors)} errors.")
    print(f"Results in {args.out}/")


if __name__ == "__main__":
    main()
