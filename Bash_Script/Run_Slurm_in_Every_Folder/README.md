# Automate SLURM job submissions across multiple simulation folders

# 📌 Overview

This script allows you to quickly submit SLURM jobs for multiple simulation folders (e.g. `simulation_1`, `simulation_2`, …).
It is designed for HPC environments where each folder contains its own slurm.sh job script.



# 🚀 Features
-	✅ Supports range mode (e.g. simulation_1 → simulation_100)
- ✅ Supports list mode (e.g. simulation_3, simulation_7, simulation_12)
- ✅ Automatically checks if slurm.sh exists before submission
- ✅ Simple and portable Bash script


# 🛠️ Requirements
  •	Bash (available by default in Linux/macOS)
	•	SLURM workload manager (for sbatch)
	•	Folder structure:

```parent_directory/
 
├── simulation_1/
│   └── src/
│       └── slurm.sh
├── simulation_2/
│   └── src/
│       └── slurm.sh
└── ...
```

# ⚡ Usage

## 1️⃣ Make it executable
``` bash
chmod +x run_every_folder.sh
```

## 2️⃣ Run in range mode

Submit jobs from `simulation_1` to `simulation_100`:
```bash
./run_every_folder.sh range 1 100
```

## 3️⃣ Run in list mode

Submit jobs for specific folders:
```bash
./run_every_folder.sh list 3 7 12
```

If arguments are invalid, the script will print usage instructions.


# 🧩 Example Output
```
✅ Submitting slurm.sh in simulation_1/src
✅ Submitting slurm.sh in simulation_2/src
⚠️  slurm.sh not found in simulation_3/src
✅ Submitting slurm.sh in simulation_4/src
🎯 Job submission completed.
```

# 🏗 Script Structure
```
run_every_folder.sh
│
├─ BASE_DIR              # Stores current directory
├─ submit_jobs()         # Loops through selected folders and submits jobs
├─ range mode logic      # Handles consecutive folder submissions
├─ list mode logic       # Handles custom folder list
└─ usage instructions    # Prints help if input is invalid
```
