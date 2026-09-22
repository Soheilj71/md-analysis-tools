#!/usr/bin/env python3
"""
find_best_checkpoint.py

A beginner-friendly utility that helps you do this:

1) Look through PyTorch Lightning CSV logs (metrics.csv) from multiple runs
2) Find the "best" value of a metric you choose (e.g., lowest train/loss)
3) Determine which epoch that best value belongs to
4) Find a checkpoint file (*.ckpt) for that epoch inside your checkpoint folder
5) Create a symlink (shortcut) named "best.ckpt" pointing to the chosen checkpoint
6) Print a command you can run for sampling/inference
   (or optionally run it automatically)

This is useful when you have many Lightning runs (version_0, version_1, ...)
and you want a quick “best checkpoint” link for downstream scripts.

Works best with folder structures like:

lightning_logs/
  version_0/metrics.csv
  version_1/metrics.csv
  ...

storage/train/
  .../epoch=12-step=1234.ckpt
  .../epoch=15-step=2345.ckpt
  ...

Author: (you)
License: (choose one, e.g., MIT)
"""

from __future__ import annotations

import argparse
import csv
import datetime
import glob
import math
import os
import sys
from typing import Dict, List, Optional, Tuple


# -----------------------------
# Small helper functions
# -----------------------------

def fail(message: str, exit_code: int = 1) -> None:
    """
    Print an error message and stop the program.

    We use sys.stderr so the message is clearly marked as an error in terminals and logs.
    """
    print(f"[ERROR] {message}", file=sys.stderr)
    sys.exit(exit_code)


def human_time(unix_ts: float) -> str:
    """
    Convert a UNIX timestamp (seconds since 1970) into a readable local time string.
    """
    return datetime.datetime.fromtimestamp(unix_ts).strftime("%Y-%m-%d %H:%M:%S")


def safe_float(text: str) -> Optional[float]:
    """
    Try to convert text to float.
    If it fails, return None instead of crashing.
    """
    try:
        return float(text)
    except Exception:
        return None


def normalize_epoch(epoch_text: str) -> str:
    """
    Make epoch text look consistent.

    Examples:
      " 12 " -> "12"
      "12.0" -> "12"  (sometimes Lightning logs epoch as 12.0)
    """
    s = (epoch_text or "").strip()
    if s == "":
        return ""

    # If it's a float that looks like an integer (e.g., "12.0"), convert to "12"
    v = safe_float(s)
    if v is not None:
        if abs(v - round(v)) < 1e-9:
            return str(int(round(v)))
        # If it is not an integer-like float, keep a compact string
        return str(v)

    return s


# -----------------------------
# Core logic
# -----------------------------

def scan_lightning_metrics_for_best(
    logdir: str,
    metric_name: str,
    mode: str,
) -> Tuple[str, str, float, float, str]:
    """
    Scan all version_* folders under `logdir` and find the best metric value.

    Returns:
      (best_version_dir, best_epoch, best_value, metrics_csv_mtime, metrics_csv_path)

    - mode="min": smaller metric value is better (common for loss)
    - mode="max": larger metric value is better (common for accuracy)
    """
    if not os.path.isdir(logdir):
        fail(f"Log directory not found: {logdir}")

    # Find run folders like lightning_logs/version_0, lightning_logs/version_1, ...
    versions = sorted(glob.glob(os.path.join(logdir, "version_*")))
    if not versions:
        fail(f"No version_* folders found inside: {logdir}")

    # Initialize "best value" depending on the mode
    best_value = math.inf if mode == "min" else -math.inf

    # Keep details of the best row we find
    best_row: Optional[Dict[str, str]] = None
    best_version_dir: Optional[str] = None
    best_metrics_csv: Optional[str] = None

    for ver_dir in versions:
        metrics_csv = os.path.join(ver_dir, "metrics.csv")
        if not os.path.isfile(metrics_csv):
            # Not all version folders always have a metrics.csv; skip safely.
            continue

        with open(metrics_csv, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # row is a dictionary: column_name -> value_as_text
                raw = (row.get(metric_name) or "").strip()
                if raw == "":
                    continue

                value = safe_float(raw)
                if value is None:
                    continue

                # Decide if this row is better than the current best
                is_better = (value < best_value) if mode == "min" else (value > best_value)
                if is_better:
                    best_value = value
                    best_row = row
                    best_version_dir = ver_dir
                    best_metrics_csv = metrics_csv

    if best_row is None or best_version_dir is None or best_metrics_csv is None:
        fail(
            f"Could not find any numeric values for metric '{metric_name}' "
            f"in any metrics.csv under: {logdir}"
        )

    # Determine the epoch for the best row
    epoch = normalize_epoch(best_row.get("epoch", ""))

    # If epoch is missing, try a fallback approach:
    # find the most common epoch value in that metrics.csv file.
    if epoch == "":
        epoch_counts: Dict[str, int] = {}
        with open(best_metrics_csv, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                e = normalize_epoch(row.get("epoch", ""))
                if e != "":
                    epoch_counts[e] = epoch_counts.get(e, 0) + 1

        if not epoch_counts:
            fail(
                f"'epoch' column is missing or empty in {best_metrics_csv}. "
                f"Cannot determine the epoch of the best metric value."
            )

        # Choose the epoch that appears most frequently
        epoch = max(epoch_counts.items(), key=lambda kv: kv[1])[0]

    # Record metrics.csv file modified time.
    # We will use this timestamp to choose the checkpoint closest in time.
    mtime = os.path.getmtime(best_metrics_csv)

    return best_version_dir, epoch, best_value, mtime, best_metrics_csv


def find_checkpoint_for_epoch(
    storage_root: str,
    epoch: str,
    ref_time: float,
) -> Tuple[str, List[str]]:
    """
    Search for checkpoint files under `storage_root` that match a target epoch.

    We first try patterns like:
      epoch=12*.ckpt

    If none are found, we try a fallback that also accepts:
      epoch_12*.ckpt
      and other names that still include the epoch

    Then we pick the checkpoint whose modified time (mtime) is closest to ref_time.

    Returns:
      (chosen_checkpoint_path, all_candidates_sorted_by_time_distance)
    """
    if not os.path.isdir(storage_root):
        fail(f"Checkpoint storage root not found: {storage_root}")

    # Common Lightning naming pattern:
    # .../epoch=12-step=1234.ckpt
    pattern = os.path.join(storage_root, "**", f"epoch={epoch}*.ckpt")
    candidates = glob.glob(pattern, recursive=True)

    # If nothing found, try a looser pattern
    if not candidates:
        alt_pattern = os.path.join(storage_root, "**", f"*{epoch}*.ckpt")
        alt = glob.glob(alt_pattern, recursive=True)

        # Keep only those that look like an epoch match
        candidates = []
        for p in alt:
            base = os.path.basename(p)
            if f"epoch={epoch}" in base or f"epoch_{epoch}" in base:
                candidates.append(p)

    if not candidates:
        fail(f"No checkpoints found for epoch '{epoch}' under: {storage_root}")

    # Sort by closeness to the metrics.csv file time
    def time_distance(path: str) -> float:
        return abs(os.path.getmtime(path) - ref_time)

    candidates.sort(key=time_distance)
    chosen = candidates[0]
    return chosen, candidates


def create_symlink(target_path: str, link_path: str) -> Tuple[str, str]:
    """
    Create (or replace) a symlink file named link_path pointing to target_path.

    A symlink is like a shortcut. Many tools/scripts can always load best.ckpt,
    while you can freely change which real checkpoint it points to.

    Returns:
      (absolute_target_path, absolute_link_path)
    """
    abs_target = os.path.abspath(target_path)
    abs_link = os.path.abspath(link_path)

    # If link_path already exists (file or symlink), remove it.
    if os.path.islink(link_path) or os.path.exists(link_path):
        try:
            os.remove(link_path)
        except OSError as e:
            fail(f"Could not remove existing link/file '{link_path}': {e}")

    try:
        os.symlink(abs_target, link_path)
    except OSError as e:
        # On Windows, symlink creation may require admin privileges.
        fail(
            f"Could not create symlink '{link_path}' -> '{abs_target}'.\n"
            f"Reason: {e}\n"
            f"If you are on Windows, you may need Administrator privileges, or use --copy instead."
        )

    return abs_target, abs_link


def copy_checkpoint(target_path: str, out_path: str) -> Tuple[str, str]:
    """
    Copy the checkpoint file instead of creating a symlink.

    This is helpful on systems where symlinks are restricted.

    Returns:
      (absolute_target_path, absolute_out_path)
    """
    import shutil

    abs_target = os.path.abspath(target_path)
    abs_out = os.path.abspath(out_path)

    try:
        shutil.copy2(abs_target, abs_out)
    except OSError as e:
        fail(f"Could not copy checkpoint '{abs_target}' -> '{abs_out}': {e}")

    return abs_target, abs_out


# -----------------------------
# Command-line interface (CLI)
# -----------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """
    Define command-line arguments.
    """
    ap = argparse.ArgumentParser(
        description="Find the best Lightning run by metric, link/copy its checkpoint as best.ckpt, and optionally run a sampler."
    )

    ap.add_argument(
        "--logdir",
        default="lightning_logs",
        help="Folder that contains lightning_logs/version_*/metrics.csv (default: lightning_logs)",
    )
    ap.add_argument(
        "--storage",
        default="storage/train",
        help="Root folder where checkpoints (*.ckpt) are stored (default: storage/train)",
    )
    ap.add_argument(
        "--metric",
        default="train/loss",
        help="Metric column name in metrics.csv (default: train/loss)",
    )
    ap.add_argument(
        "--mode",
        choices=["min", "max"],
        default="min",
        help="How to select the best value: min (smaller is better) or max (larger is better) (default: min)",
    )
    ap.add_argument(
        "--output",
        default="best.ckpt",
        help="Name of the symlink/copy file to create (default: best.ckpt)",
    )
    ap.add_argument(
        "--sampler",
        default="sampling.py",
        help="Sampler/inference script to run after selecting checkpoint (default: sampling.py)",
    )
    ap.add_argument(
        "--run",
        action="store_true",
        help="If provided, automatically execute the sampler script after creating best.ckpt",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="If provided, do not create link/copy; only print what would happen",
    )
    ap.add_argument(
        "--copy",
        action="store_true",
        help="Copy the checkpoint file instead of creating a symlink (useful on Windows or restricted systems)",
    )

    return ap


def main() -> None:
    """
    Main program entry point.
    """
    args = build_arg_parser().parse_args()

    print(f"[1/4] Scanning logs in: {args.logdir}")
    print(f"      Looking for best metric: '{args.metric}' (mode: {args.mode})")

    best_version_dir, best_epoch, best_value, metrics_mtime, metrics_csv_path = scan_lightning_metrics_for_best(
        logdir=args.logdir,
        metric_name=args.metric,
        mode=args.mode,
    )

    print("      Best result found:")
    print(f"        Run folder : {best_version_dir}")
    print(f"        Metrics CSV: {metrics_csv_path}")
    print(f"        Epoch      : {best_epoch}")
    print(f"        Value      : {best_value}")
    print(f"        CSV time   : {human_time(metrics_mtime)}")

    print(f"[2/4] Searching checkpoints in: {args.storage}")
    chosen_ckpt, candidates = find_checkpoint_for_epoch(
        storage_root=args.storage,
        epoch=best_epoch,
        ref_time=metrics_mtime,
    )

    print(f"      Found {len(candidates)} candidate checkpoint(s) for epoch {best_epoch}.")
    print("      Chosen checkpoint (closest in time to metrics.csv):")
    print(f"        {chosen_ckpt}")
    print(f"        ckpt time: {human_time(os.path.getmtime(chosen_ckpt))}")

    print(f"[3/4] Preparing output file: {args.output}")

    if args.dry_run:
        print("      --dry-run enabled: not creating link/copy.")
    else:
        if args.copy:
            abs_target, abs_out = copy_checkpoint(chosen_ckpt, args.output)
            print("      Copied checkpoint file:")
            print(f"        from: {abs_target}")
            print(f"        to  : {abs_out}")
        else:
            abs_target, abs_link = create_symlink(chosen_ckpt, args.output)
            print("      Created symlink (shortcut):")
            print(f"        {abs_link} -> {abs_target}")

    # This is the command we recommend for sampling
    cmd = ["python", args.sampler, "--ckpt_path", f"./{args.output}"]

    print(f"[4/4] Ready to sample/infer.")
    print("      Command to run:")
    print(f"        {' '.join(cmd)}")

    if args.run:
        if args.dry_run:
            print("      Note: --run was provided, but --dry-run prevents execution.")
            return

        print("      --run provided: launching sampler now...")

        # os.execvp replaces the current process with the sampler process.
        # That means after launching, this script ends immediately (no return here).
        os.execvp("python", cmd)


if __name__ == "__main__":
    main()
