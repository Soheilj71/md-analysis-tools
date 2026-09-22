# 📊 Time-Series Data Plotter with Smoothing

This repository contains a Python script for reading, processing, and visualizing time-series data from a text-based file format (such as .xvg).
The script supports:
-  Reading numerical data while ignoring comment lines.
-  Plotting raw data points.
-  Adding a smoothed curve for better visualization.
-  Saving the figure as a high-resolution PNG.

## 📌 Features
-  Flexible Input: Works with any plain-text file containing at least two numeric columns (e.g., time and measurement).
-  Comment Handling: Skips lines starting with @ or # (common in simulation output files).
-  Dual Visualization:
-  Raw data as scatter points.
-  Smoothed data using a moving average filter.
-  Customizable Appearance: Easily adjust:
-  Colors, point size, line width.
-  Axis labels and title.
-  Smoothing window size.
-  High-Resolution Output: Saves plots at 300 DPI by default.


## 📂 Example File Structure
```
.
├── data.xvg            # Example input file (time vs value)
├── plot_timeseries.py  # Python plotting script
└── README.md           # Documentation
```

## ⚙️ Requirements

Install Python 3.x and dependencies:
```bash
pip install numpy matplotlib scipy
```

## 🚀 Usage
1.  Place your data file (e.g., data.xvg) in the project folder.
2.	Update the script to match your filename and desired axis labels.
3.	Run:
```python
 python plot_timeseries.py
```
4.	The script will:
-  Display the plot on screen.
-  Save it as output.png.


## 🖼 Example Output

-  Scatter points: Raw values from the file.
-  Smooth curve: Moving average filtered values for trend visualization.

<img width="720" height="480" alt="pressure" src="https://github.com/user-attachments/assets/1c9f5f67-2f60-42a5-b847-08a3592b7acc" />

## 🧪 Notes
-  Works for any simulation or experiment output in a simple numeric two-column format.
-  Change uniform_filter1d(y, size=10) in the code to adjust smoothing.
-  Supports plotting different variables by changing labels and column selections.
 
