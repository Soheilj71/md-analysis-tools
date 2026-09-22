# Written by Soheil Jamali
# sjamali@uark.edu, soheil.jamali.dev@gmail.com
# University of Arkansas, Fayetteville, AR, USA

"""
General-purpose time-series plotter with smoothing.
- Reads a two-column data file (e.g., time vs. measurement).
- Skips comment lines starting with '@' or '#'.
- Plots raw data as scatter points and a smoothed curve.
- Saves the plot as a high-resolution PNG.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

# ===== User Configurations =====
input_file = 'data.xvg'        # Input file name
output_file = 'output.png'     # Output PNG file name
x_label = 'X-axis'             # Label for X-axis
y_label = 'Y-axis'             # Label for Y-axis
plot_title = 'Data Visualization'  # Plot title
smooth_window = 10             # Smoothing window size (higher = smoother)
scatter_color = 'black'        # Color for scatter points
line_color = 'blue'            # Color for smoothed line
point_size = 10                # Scatter point size
line_width = 1.5               # Line thickness
dpi_value = 300                # DPI for saved PNG
# ===============================

# Load data, skipping comment lines
data = np.loadtxt(input_file, comments=['@', '#'])

# Ensure at least two columns
if data.shape[1] < 2:
    raise ValueError("The input file must have at least two columns.")

# First column = X, second column = Y
x = data[:, 0]
y = data[:, 1]

# Apply smoothing filter
y_smooth = uniform_filter1d(y, size=smooth_window)

# Create the plot
plt.scatter(x, y, color=scatter_color, s=point_size, label='Raw data')
plt.plot(x, y_smooth, color=line_color, linewidth=line_width, label='Smoothed')

# Add labels and title
plt.xlabel(x_label, fontsize=14)
plt.ylabel(y_label, fontsize=14)
plt.title(plot_title, fontsize=16)

# Add legend
plt.legend()

# Adjust layout, save, and show
plt.tight_layout()
plt.savefig(output_file, dpi=dpi_value)
plt.show()
