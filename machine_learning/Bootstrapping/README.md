# bootstrap.py

Bootstrap confidence intervals for any statistic of sampled data: KL or
Jensen-Shannon divergence against a reference distribution (Mueller-Brown
potential, a free-energy grid, or reference samples), or any Python function
you supply.

Needs only `numpy` (`matplotlib` if you pass `--plot`).

## Quick start

```bash
# Bootstrap your own statistic, one confidence interval per file
python bootstrap.py --input 'runs/*.npy' --stat examples/my_stats.py:mean_x

# KL(samples || reference samples) for two conditions
python bootstrap.py \
    --input modelA='results/modelA/*.npy' --input modelB='results/modelB/*.npy' \
    --reference samples --ref-file reference.npy --range -3 3 -3 3 --bins 100 \
    --out results/kl --plot

# Everything from a config file
python bootstrap.py --config examples/config.json

# Check which files match before running
python bootstrap.py --config examples/config.json --dry-run
```
## What it does

For every input file it draws `--n-boot` replicates by resampling with
replacement, evaluates the statistic on each, and reports:

| column | meaning |
|---|---|
| `KL_orig` | statistic on the original, un-resampled data |
| `KL_mean`, `KL_std` | mean and standard deviation over replicates |
| `KL_lo95`, `KL_hi95` | percentile confidence interval (`--ci`, default 95) |
| `CI_width` | `hi - lo` |
| `n_points`, `n_traj`, `out_of_window` | sample size, trajectories, points outside the histogram window |
| `T`, `N`, ... | labels parsed from the file name with `--label-regex` |

## Options that matter

**Inputs.** `--input NAME=GLOB` can be repeated; each name is a condition with
its own output folder. `**` in a glob recurses. Files can be `.npy`, `.npz`
(`--key`), `.csv` or whitespace text. The last axis is the coordinate axis, so
`(n_traj, n_steps, 1, 2)` and `(N, 2)` both work. `--columns` selects
coordinates.

**Labels and filtering.** `--label-regex` turns file names into columns using
named groups: `'T(?P<T>\d+)_N(?P<N>\d+)'` gives `run_T300_N64.npy` the labels
`T=300, N=64`. `--where 'T >= 300'` filters on them, and `--pivot T N` writes
heatmap tables with T as rows and N as columns.

**Resampling unit.** `--resample frames` (default) resamples individual points.
`--resample trajectories` resamples whole trajectories, which keeps the time
correlation within each trajectory and gives honest (wider) intervals for
correlated data. `--n-per-replicate` sets how many trajectories are drawn.

**Statistic.**
- `--stat kl` / `--stat js` use a histogram against `--reference`:
  - `muller`: analytic Mueller-Brown Boltzmann density, a standard 2-D benchmark (`--beta`, `--grid-steps`), on `--range`/`--bins`
  - `grid`: probabilities stored on a regular grid in an `.npz` (`--grid-keys` names the axis arrays, `--weights-key` the probabilities); the grid defines the bins
  - `samples`: histogram of reference samples (`--ref-file`, `--ref-key`) on `--range`/`--bins`
- `--stat FILE.py:FUNC` bootstraps any function `FUNC(x: (N, d) array) -> float`.
  See `examples/my_stats.py`.

**Histogram details.** Empty bins are floored at `--eps` (sample side) and
`--ref-eps` (reference side, defaults to `--eps`), then renormalised. By
default, points outside the window go to one extra overflow bin that the
reference gives ~0 probability, so leaving the window is penalised.
`--no-overflow` drops those points instead.

**Ranking.** `--best min` (default) reports, for each condition, the file with
the lowest mean and whether its CI is separated from the runner-up's
(`best_summary.csv`). Use `--best max` for statistics where larger is better, or `none`.

## Outputs (`--out`)

```
<out>/
  bootstrap_all.csv          every file, all conditions
  best_summary.csv           best vs runner-up per condition
  run_config.json            full settings, versions, timestamp, errors
  <condition>/
    bootstrap_summary.csv
    heatmap_mean.csv  heatmap_std.csv  heatmap_ci_width.csv   (with --pivot; + .png with --plot)
    replicates/*.npy         with --save-replicates
```

## Reproducibility and speed

- Each file gets its own random stream, seeded from `--seed`, the condition
  name and the file name. A file's result does not depend on which other files
  are in the run or on `--workers`.
- For `kl`/`js` with frame resampling, the histogram of *n* points drawn with
  replacement is sampled directly as `Multinomial(n, counts / n)`. That has
  exactly the same distribution as resampling the points and re-histogramming,
  but costs O(bins) instead of O(n) per replicate, so files with millions of
  points bootstrap in seconds.
- Files run in parallel (`--workers`, default: all cores but one).
