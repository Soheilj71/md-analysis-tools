# Written by Soheil Jamali
# Email: sjamali@uark.edu, soheil.jamali.dev@gmail.com
# University of Arkansas, Fayetteville, AR, USA

"""
General-purpose script for reading and plotting two-column data files.
- Works with .xvg or any plain-text numeric file.
- Skips comment lines starting with '@' or '#'.
- Plots the first column on the X-axis and the second column on the Y-axis.
- Saves the figure as a PNG file.
"""

import numpy as np
import matplotlib.pyplot as plt

# ===== User Configurations =====
input_file = 'data.xvg'           # Input file name
output_file = 'plot.png'          # Output PNG file name
x_label = 'X-axis'                # Label for X-axis
y_label = 'Y-axis'                # Label for Y-axis
plot_title = 'Data Visualization' # Plot title
# ===============================

# Load data, skipping comment lines
data = np.loadtxt(input_file, comments=['@', '#'])

# Ensure the file has at least two columns
if data.shape[1] < 2:
    raise ValueError("The input file must have at least two columns.")

# Extract first and second columns
x = data[:, 0]
y = data[:, 1]

# Create plot
plt.plot(x, y)
plt.xlabel(x_label)
plt.ylabel(y_label)
plt.title(plot_title)

# Save and show plot
plt.savefig(output_file)
plt.show()
