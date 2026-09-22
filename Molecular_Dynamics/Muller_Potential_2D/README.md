# Müller Potential Visualization

This repository contains a Python implementation and visualization of the **Müller potential**, a classical two-dimensional energy landscape widely used in molecular dynamics and sampling studies.

The Müller potential is commonly used as a benchmark system for:
- Molecular Dynamics (MD)
- Transition path sampling
- Enhanced sampling techniques
- Diffusion models and generative modeling
- Free energy surface analysis

---

## 📖 What is the Müller Potential?

The Müller potential is a synthetic 2D energy surface composed of four Gaussian-like terms.  
It contains:

- Multiple local minima
- Saddle points
- Energy barriers

Because of its non-trivial topology, it is frequently used to test sampling efficiency and rare-event methods.

---

## 📂 Repository Structure

├── muller_potential.py           # Main script for computing and plotting the surface

└── README.md


---

## ⚙️ Requirements

This project requires only standard scientific Python libraries:

```bash
pip install numpy matplotlib
```

---

## ▶️ How to Run

Run the script directly:
```python
python muller_potential.py
```
The script will:

- Compute the potential on a 2D grid

- Generate a heatmap visualization

- Overlay contour lines

- Display the energy surface

---

## 📐 Computational Domain

The potential is computed over:

```python
x ∈ [-1.5, 1.2]
y ∈ [-1.0, 2.2]
```

The resolution can be adjusted inside the script:

```python
resolution = 400
```

Higher resolution produces smoother figures but increases computation time.

---

## 🎨 Visualization Details

The figure includes:

- Heatmap (energy surface)

- Contour lines (constant energy levels)

- Colorbar

- Adjustable aspect ratio

- Customizable figure dimensions

To change figure size:
```python
fig, ax = plt.subplots(figsize=(10, 6))
```

To preserve physical scaling:
```python
ax.set_aspect("equal")
```

---

## 📸 Example Output

The output is a 2D energy landscape with multiple minima and transition pathways between them.

<img width="600" height="450" alt="muller_potential" src="https://github.com/user-attachments/assets/d629e669-68cd-4464-a00c-6dcb28206146" />

---

## 🧪 Why This Is Useful

The Müller potential is frequently used in:

- Testing enhanced sampling algorithms

- Benchmarking diffusion models in molecular dynamics

- Studying rare-event transitions

Comparing free energy reconstruction methods
