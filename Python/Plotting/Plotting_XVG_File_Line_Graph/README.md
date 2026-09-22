# 📊 General-Purpose Data Plotter

This repository contains a simple Python script for reading and plotting **two-column numeric data** from `.xvg` or other plain-text files.  
It can be used for **simulation outputs, experimental results, sensor data**, or any similar format.

## 📌 Features
- Reads `.xvg` or any text-based numeric file.
- Skips comment lines starting with `@` or `#`.
- Plots first column as X-axis and second as Y-axis.
- Saves the plot as a PNG image.
- Fully customizable labels, title, and file names.

---

## ⚙️ Requirements
Install Python 3.x and dependencies:
```bash
pip install numpy matplotlib
```

## 🚀 Usage
1. Place your data file (e.g., data.xvg) in the same folder as the script.
2.	Edit the configuration section in the script:

```python
input_file = 'data.xvg'
output_file = 'plot.png'
x_label = 'Time (ps)'
y_label = 'Pressure (bar)'
plot_title = 'Pressure, NPT Equilibration'
```

3. Run:
 ```bash
python plot_data.py
```

4.	The plot will be:
- Displayed in a pop-up window.
- Saved as the specified PNG file.


## 📂 Example File Structure
```
.
├── data.xvg         # Example input file
├── plot_data.py     # Python plotting script
└── README.md        # Documentation
```

## 🧪 Notes
- Works with any two-column numeric dataset.
- For .xvg files, you can generate them in GROMACS with:

 ```bash
gmx energy -f npt.edr -o pressure.xvg
```

- Change axis labels and plot title to match your data type (e.g., Time vs RMSD, Distance vs Energy).
