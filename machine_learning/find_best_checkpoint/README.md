# Find Best PyTorch Lightning Checkpoint (Beginner-Friendly)

This tool scans PyTorch Lightning CSV logs (`metrics.csv`) across multiple runs and automatically finds the checkpoint for the **best** metric value (for example, the lowest `train/loss`). Then it creates a file called `best.ckpt` (a symlink/shortcut or a copy) so your sampling/inference scripts can always load the best checkpoint easily.

---

## What problem does this solve?

When you train many Lightning runs, you usually get folders like:
```
lightning_logs/
version_0/metrics.csv
version_1/metrics.csv
```

And your checkpoints might be somewhere else, like:

```
storage/train/
.../epoch=10-step=....ckpt
.../epoch=15-step=....ckpt

```


Manually finding the best checkpoint is annoying.

This script does it for you.

---

## What this script does (step-by-step)

1. Looks inside `lightning_logs/version_*/metrics.csv`
2. Searches for your chosen metric column (default: `train/loss`)
3. Picks the best value:
   - `--mode min` → smallest value is best (good for loss)
   - `--mode max` → largest value is best (good for accuracy)
4. Finds the epoch number for that best row
5. Searches your checkpoint folder for checkpoint files matching that epoch
6. If there are multiple matches, it chooses the checkpoint whose file time is closest to the `metrics.csv` file time (helps match the correct run)
7. Creates:
   - a symlink (shortcut) named `best.ckpt` (default)
   - OR a copied file named `best.ckpt` if you use `--copy`
8. Prints a ready-to-run command for your sampler:
```bash
python sampling.py --ckpt_path ./best.ckpt
```

9. Optionally runs the sampler if you add `--run`

---

## Requirements

- Python 3.8+ recommended
- Your training logs must include:
- `lightning_logs/version_*/metrics.csv`
- Your checkpoint files must exist under a directory like:
- `storage/train/`
- Checkpoint filenames should typically include the epoch, for example:
- `epoch=12-step=1234.ckpt`
- or `epoch_12.ckpt`

---

## Installation

Just copy `find_best_checkpoint.py` into your project (for example into a `tools/` folder).

Make it executable (optional on Linux/Mac):

```bash
chmod +x find_best_checkpoint.py
```
# Basic Usage

From your project root (where `lightning_logs/` exists):
```bash
python find_best_checkpoint.py
```

This will:
* find the best `train/loss` (minimum) across all versions
* find the checkpoint for that epoch under `storage/train`
* create `best.ckpt`
* print a sampling command

# Common Examples

## 1) Use validation loss instead of train loss
```bash
python find_best_checkpoint.py --metric "val/loss" --mode min
```

## 2) Use accuracy and maximize it
```bash
python find_best_checkpoint.py --metric "val/acc" --mode max
```

## 3) Change log folder and checkpoint folder
```bash
python find_best_checkpoint.py --logdir my_logs --storage my_checkpoints
```

## 4) Do not create best.ckpt, only show what would happen
```bash
python find_best_checkpoint.py --dry-run
```

## 5) Copy the checkpoint instead of creating a symlink
Symlinks can be restricted on some systems (especially Windows). Use `--copy`:
```bash
python find_best_checkpoint.py --copy
```

## 6) Automatically run your sampler/inference script
```bash
python find_best_checkpoint.py --sampler sampling.py --run
```

This will execute:
```bash
python sampling.py --ckpt_path ./best.ckpt
```

# Output Files
* `best.ckpt` (default)
    * By default it is a symlink/shortcut pointing to the chosen checkpoint.
    * If you use `--copy`, it becomes a real copied checkpoint file.

# Troubleshooting
## No version_* folders found
Make sure your logs directory is correct:
    * Default: `lightning_logs`
    * If your folder is different, use `--logdir YOUR_FOLDER`

## No numeric values for metric found
Make sure the metric column exists in `metrics.csv`.
Open one `metrics.csv` and check the column names.

Example:
* `train/loss`
* `val/loss`
* `val/acc`

## No checkpoints found for epoch”
Make sure:
    * your checkpoint folder is correct (`--storage`)
    * the checkpoint files include epoch in the filename
        * like `epoch=12...ckpt`

# Symlink creation fails on Windows
Use:
```bash
python find_best_checkpoint.py --copy
```

# Recommended GitHub Placement
A common clean structure:
```
your_repo/
  tools/
    find_best_checkpoint.py
  README.md
  sampling.py
  lightning_logs/
  storage/
```
