#!/usr/bin/env python3
"""
===============================================================================
COMPUTE KL DIVERGENCE BETWEEN TWO DATASETS
-------------------------------------------------------------------------------
Purpose:
    Compute KL divergence between two datasets using histogram estimation.

Supports:
    - 2D data (e.g., Müller potential, MD projections)
    - Trajectory data (n_traj, n_steps, 2)

Usage:
    python compute_kl_divergence.py data1.npy data2.npy

Example:
    python compute_kl_divergence.py real.npy synthetic.npy
===============================================================================
"""

import numpy as np
import sys


def fail(msg):
    print(f"Error: {msg}")
    sys.exit(1)


def load_data(path):
    """Load numpy data and reshape if needed."""
    data = np.load(path)

    # If trajectory shape (n_traj, n_steps, 2)
    if data.ndim == 4:
        data = data.reshape(-1, 2)
    elif data.ndim == 3:
        data = data.reshape(-1, 2)

    if data.shape[1] != 2:
        fail(f"{path} must have shape (*, 2)")

    return data


def compute_histogram(data, x_edges, y_edges):
    """Compute normalized 2D histogram."""
    H, _, _ = np.histogram2d(
        data[:, 0],
        data[:, 1],
        bins=[x_edges, y_edges],
        density=True
    )
    return H


def kl_divergence(P, Q, epsilon=1e-12):
    """
    Compute KL divergence: KL(P || Q)
    """
    P = P + epsilon
    Q = Q + epsilon

    return np.sum(P * np.log(P / Q))


def main():
    if len(sys.argv) != 3:
        fail("Usage: python compute_kl_divergence.py data1.npy data2.npy")

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    # Load data
    data1 = load_data(file1)
    data2 = load_data(file2)

    print(f"Data1 shape: {data1.shape}")
    print(f"Data2 shape: {data2.shape}")

    # -------------------------------------------------------------------------
    # DEFINE COMMON BIN EDGES (VERY IMPORTANT)
    # -------------------------------------------------------------------------
    combined = np.vstack([data1, data2])

    x_min, x_max = combined[:, 0].min(), combined[:, 0].max()
    y_min, y_max = combined[:, 1].min(), combined[:, 1].max()

    bins = 150  # you can tune this

    x_edges = np.linspace(x_min, x_max, bins)
    y_edges = np.linspace(y_min, y_max, bins)

    # -------------------------------------------------------------------------
    # COMPUTE HISTOGRAMS
    # -------------------------------------------------------------------------
    P = compute_histogram(data1, x_edges, y_edges)
    Q = compute_histogram(data2, x_edges, y_edges)

    # Normalize (extra safety)
    P /= np.sum(P)
    Q /= np.sum(Q)

    # -------------------------------------------------------------------------
    # COMPUTE KL
    # -------------------------------------------------------------------------
    kl_pq = kl_divergence(P, Q)
    kl_qp = kl_divergence(Q, P)

    print("\nResults:")
    print(f"KL(P || Q) = {kl_pq:.6f} nats")
    print(f"KL(Q || P) = {kl_qp:.6f} nats")


if __name__ == "__main__":
    main()
