# 2D KL Divergence with Bootstrap Confidence Interval

Compute KL divergence between two 2D datasets (e.g., real vs synthetic trajectories) using histogram discretization and estimate uncertainty using bootstrap confidence intervals.

This tool is especially useful for:
* Comparing real molecular dynamics (MD) trajectories vs synthetic trajectories
* Evaluating generative models (e.g., diffusion models, VAEs, GANs)
* Quantifying distribution mismatch in 2D phase space
* Estimating statistical uncertainty using bootstrap resampling

# 📌 What This Script Does

Given two `.npy` files containing 2D samples:
1. Loads and cleans the datasets
2. Converts them into 2D histograms (probability grids)
3. Computes:

$$
KL(P_{\text{real}} \parallel P_{\text{synth}}) 
$$

4. Performs bootstrap resampling
5. Reports a 95% confidence interval (percentile method)
6. Optionally:
      * Saves results to CSV
      * Saves a scatter plot for visual inspection

# 📂 Supported Input Formats
The script accepts `.npy` files shaped as:

## ✔ Option 1: Flat point cloud
`(N, 2)`

Each row is one `(x, y)` sample.

## ✔ Option 2: Trajectory format
`(n_traj, n_steps, 2)`

Automatically flattened into `(N, 2)`.

This makes it suitable for MD trajectories and generative model outputs.

# 📦 Installation
## Requirements
* Python ≥ 3.8
* NumPy

## Optional:
* Matplotlib (only needed if using `--plot`)

## Install Dependencies
```bash
pip install numpy
```

## Optional plotting:

```bash
pip install matplotlib
```

# 🚀 Usage

Basic example:
```bash
python kl_2d_bootstrap.py \
    --real real_data.npy \
    --synth synthetic_data.npy
```

## ⚙ Available Arguments
| Argument	| Description	                              | Default  |
|----------|-------------------------------------------|----------|
|--real	   | Path to real dataset (.npy)	              | required |
|--synth	  | Path to synthetic dataset (.npy)          |	required |
|--bins	   | Histogram bins per dimension	             | 60       |
|--eps	    | Small smoothing value to avoid zero bins	 | 1e-12    |
|--n_boot	 | Number of bootstrap resamples	            | 200      |
|--seed	   | Random seed for reproducibility	          | 0        | 
|--out_csv	| Save summary results to CSV	              | (none)   | 
|--plot	   | Save scatter comparison plot	             | (none)   |

# 🧠 Example with All Options
```bash
python kl_2d_bootstrap.py \
    --real real.npy \
    --synth synth.npy \
    --bins 80 \
    --n_boot 500 \
    --out_csv results/summary.csv \
    --plot results/comparison.png
```

Output:
```
KL divergence (nats):
  KL(P_real || P_synth) = 0.013421
Bootstrap 95% CI (percentile):
  [0.01092, 0.01683]
Wrote CSV: results/summary.csv
Wrote plot: results/comparison.png
```

# 📊 What the Output Means
## KL Divergence (nats)
Measures how different the synthetic distribution is from the real one.
* 0 → identical distributions
* Small value → good match
* Large value → strong mismatch
Units: **nats** (natural logarithm base e)

# Bootstrap 95% Confidence Interval
Estimated uncertainty from resampling:
* Lower bound
* Upper bound
Gives statistical reliability of the KL estimate.

# 🧮 Mathematical Background
## Discrete KL Divergence
After histogram discretization:

$$
KL(P \parallel Q) = \sum_{i} P_i \log\left(\frac{P_i}{Q_i}\right)
$$

Where:

- $P_i$ = Probability of bin $i$ from the **real** dataset  
- $Q_i$ = Probability of bin $i$ from the **synthetic** dataset  

A small epsilon is added to all bins to prevent division by zero.


# Bootstrap Procedure
For each bootstrap iteration:
1. Sample real data with replacement
2. Sample synthetic data with replacement
3. Recompute KL
4. Store value
Confidence intervals are computed using percentile bounds.

# 📁 CSV Output Format
If `--out_csv` is used, a one-row CSV is written:
| Column                 |	Meaning                     |
|------------------------|-----------------------------|
|real_file	              | Path to real input          |
|synth_file	             | Path to synthetic input     |
|bins	                   | Histogram resolution        |
|eps	                    | Smoothing value             |
|n_boot	                 | Number of bootstrap samples |
|seed	                   | Random seed                 |
|kl_point_nats	          | KL estimate                 |
|ci95_lo_nats	           | CI lower bound              |
|ci95_hi_nats	           | CI upper bound              |

Useful for hyperparameter sweeps or benchmarking experiments.

# 🎯 When Should You Use This?
This tool is appropriate when:
* Comparing synthetic MD trajectories to ground truth
* Evaluating generative models in low-dimensional phase space
* Studying free energy surface reconstruction quality
* Quantifying distribution learning performance

# ⚠ Limitations
* Histogram-based KL depends on bin size.
* High-dimensional data is not supported (2D only).
* Very small datasets may produce unstable estimates.

# 📌 Best Practices
* Try multiple `--bins` values to check stability.
* Increase `--n_boot` for more reliable CI (e.g., 500–1000).
* Ensure both datasets share similar support regions.
* Always inspect the optional scatter plot.

# 👤 Author
Soheil Jamali

PhD Researcher — Molecular Dynamics & Generative Modeling

