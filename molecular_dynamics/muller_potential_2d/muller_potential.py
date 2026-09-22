"""
Müller Potential Visualization
-------------------------------

This script computes and visualizes the Müller potential,
which is a well-known 2D energy landscape used in molecular
dynamics and sampling studies.

The Müller potential contains multiple minima and saddle points,
making it a standard benchmark for testing algorithms such as:
- Molecular Dynamics
- Transition Path Sampling
- Diffusion Models
- Enhanced Sampling Methods

The script:
1. Defines the Müller potential function
2. Creates a 2D grid over a chosen domain
3. Computes the potential energy at each grid point
4. Visualizes the surface using a heatmap + contour lines

The full requested domain is:
    x ∈ [-1.5, 1.2]
    y ∈ [-1.0, 2.2]

Author: Soheil Jamali
"""

import numpy as np
import matplotlib.pyplot as plt


def muller_potential(x, y):
    """
    Computes the Müller potential energy at coordinates (x, y).

    The potential is defined as a sum of four Gaussian-like terms.
    Each term contributes to the overall shape of the energy landscape.

    Parameters
    ----------
    x : numpy array
        x-coordinates (can be scalar or array)
    y : numpy array
        y-coordinates (same shape as x)

    Returns
    -------
    numpy array
        Potential energy values at (x, y)
    """

    # These constants define the shape of the potential surface
    aa = [-1, -1, -6.5, 0.7]
    bb = [0, 0, 11, 0.6]
    cc = [-10, -10, -6.5, 0.7]
    AA = [-200, -100, -170, 15]
    XX = [1, 0, -0.5, -1]
    YY = [0, 0.5, 1.5, 1]

    value = 0.0

    # Sum over the four Gaussian terms
    for j in range(4):
        value += AA[j] * np.exp(
            aa[j] * (x - XX[j])**2
            + bb[j] * (x - XX[j]) * (y - YY[j])
            + cc[j] * (y - YY[j])**2
        )

    return value


# -------------------------------------------------------
# Step 1: Define the computational domain (x and y limits)
# -------------------------------------------------------

minx, maxx = -1.5, 1.2
miny, maxy = -1.0, 2.2

# Number of grid points in each direction
# Higher value = smoother plot
resolution = 400

# Create evenly spaced values in x and y
x = np.linspace(minx, maxx, resolution)
y = np.linspace(miny, maxy, resolution)

# Create a 2D grid of coordinates
xx, yy = np.meshgrid(x, y)


# -------------------------------------------------------
# Step 2: Compute potential energy on the grid
# -------------------------------------------------------

V = muller_potential(xx, yy)

# Clip extremely high values to improve visualization contrast
# (otherwise color scale becomes dominated by large positive energies)
V_clipped = np.clip(V, None, 200)


# -------------------------------------------------------
# Step 3: Visualization
# -------------------------------------------------------

fig, ax = plt.subplots(figsize=(8, 6))

# Heatmap (continuous color representation of energy)
im = ax.imshow(
    V_clipped,
    extent=[minx, maxx, miny, maxy],
    origin="lower",
    cmap="plasma_r",   # reversed plasma colormap
    aspect="auto"
)

# Add contour lines (lines of constant energy)
levels = np.linspace(V_clipped.min(), V_clipped.max(), 25)
ax.contour(
    xx,
    yy,
    V_clipped,
    levels=levels,
    colors="black",
    linewidths=0.4
)

# Set axis limits explicitly (ensures full coverage of the domain)
ax.set_xlim(minx, maxx)
ax.set_ylim(miny, maxy)

# Axis labels
ax.set_xlabel("x")
ax.set_ylabel("y")

# Add colorbar to show energy scale
cbar = fig.colorbar(im, ax=ax)
cbar.set_label("Potential Energy")

# Improve spacing for saving or display
plt.tight_layout()

plt.show()

