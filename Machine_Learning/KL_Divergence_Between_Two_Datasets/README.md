# 📊 KL Divergence Calculator for Scientific Datasets

## Overview

This repository provides a simple and robust Python script to compute the **Kullback–Leibler (KL) divergence** between two datasets using **2D histogram estimation**.

The tool is particularly useful for:

* Molecular dynamics (MD) simulations
* Diffusion model validation
* Free energy surface (FES) comparison
* Any 2D probability distribution analysis

It supports both **flat datasets** and **trajectory-based data**, making it suitable for scientific workflows involving large simulation outputs.

---

## 🚀 Features

* ✅ Computes **KL(P || Q)** and **KL(Q || P)**
* ✅ Supports multiple data formats:

  * `(N, 2)` → flat data
  * `(n_traj, n_steps, 2)` → trajectory data
* ✅ Automatically reshapes trajectory data
* ✅ Uses **shared histogram bins** (critical for valid KL computation)
* ✅ Includes **numerical stability handling** (`epsilon`)
* ✅ Minimal dependencies (NumPy only)

---

## 📦 Installation

No installation required beyond Python and NumPy.

```bash
pip install numpy
```

---

## 🧠 What is KL Divergence?

KL divergence measures how one probability distribution differs from another:

* **KL(P || Q)** → How well Q approximates P
* **KL(Q || P)** → Reverse comparison

Important properties:

* Always ≥ 0
* Equals 0 only if distributions are identical
* Not symmetric

---

## ▶️ Usage

```bash
python compute_kl_divergence.py data1.npy data2.npy
```

---

## 📌 Example

```bash
python compute_kl_divergence.py real.npy synthetic.npy
```

Output:

```
Data1 shape: (100000, 2)
Data2 shape: (100000, 2)

Results:
KL(P || Q) = 0.050989 nats
KL(Q || P) = 0.043158 nats
```

---

## 📊 Input Format

### Supported shapes:

| Format                    | Description     |
| ------------------------- | --------------- |
| `(N, 2)`                  | Flat dataset    |
| `(n_traj, n_steps, 2)`    | Trajectory data |
| `(n_traj, n_steps, 1, 2)` | Also supported  |

The script automatically reshapes data into `(N, 2)`.

---

## ⚠️ Important Notes

### 1. Shared Histogram Binning

Both datasets are combined to define **common bin edges**:

```python
combined = np.vstack([data1, data2])
```

This is **essential**. Without shared bins, KL divergence becomes meaningless.

---

### 2. Numerical Stability

A small value (`epsilon = 1e-12`) is added:

```python
P = P + epsilon
Q = Q + epsilon
```

This prevents:

* `log(0)`
* division by zero

---

### 3. Interpretation of Results

| KL Value | Interpretation                 |
| -------- | ------------------------------ |
| ~0       | Almost identical distributions |
| 0.01–0.1 | Very good agreement            |
| 0.1–1    | Moderate difference            |
| >1       | Significant mismatch           |

---

## 🎯 Recommended Usage (Research Context)

If comparing **synthetic vs reference distributions**:

```text
KL(P_synth || Q_reference)
```

* Use this as your **primary metric**
* Report reverse KL as supplementary

---

## 📁 File Structure

```
.
├── compute_kl_divergence.py
├── README.md
├── data/
│   ├── real.npy
│   └── synthetic.npy
```

---

## 🔧 Customization

You can modify:

### Number of bins

```python
bins = 150
```

Higher → more resolution
Lower → smoother distribution

---

## 📈 Future Improvements (Optional)

* Bootstrap confidence intervals
* CSV export for batch runs
* Folder-based automation (e.g., multiple simulations)
* KL heatmap visualization

---
