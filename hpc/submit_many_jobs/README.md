# Submit Many SLURM Jobs

A simple Bash script to submit multiple SLURM job files at once from a folder.

This is useful when you have many job scripts and want to submit them quickly without running `sbatch` manually for each file.

---

## What this script does

This script:

1. Looks inside a folder
2. Finds all `.slurm` and `.sh` files
3. Submits each file using `sbatch`
4. Prints progress and a summary

---

## File

- `submit_many_jobs.sh`

---

## Important note (HPC compatibility)

This script is designed for HPC systems that use **SLURM**.

However, configurations may vary between clusters.

Requirements:

- SLURM installed
- `sbatch` command available

If your HPC uses a different scheduler (PBS, LSF, etc.), this script will not work.

---

## Usage

```bash
bash submit_many_jobs.sh path/to/jobs_folder
```
## Examples

Submit all jobs in a folder:

```bash
bash submit_many_jobs.sh jobs/
```

Submit jobs from a specific directory:

```bash
bash submit_many_jobs.sh ./slurm_scripts
```

## Example folder structure

```
jobs/
├── job1.slurm
├── job2.slurm
├── job3.sh
```

Running:
```bash
bash submit_many_jobs.sh jobs/
```

Will result in:
```
Submitting: jobs/job1.slurm
Submitting: jobs/job2.slurm
Submitting: jobs/job3.sh
```
## Output example
```
--------------------------------------------------
Submitting: jobs/job1.slurm
Submitted batch job 123456

--------------------------------------------------
Submitting: jobs/job2.slurm
Submitted batch job 123457

==================================================
Successfully submitted 2 job(s).
```

## Behavior notes
*   Only files with extensions:
    *   `.slurm`
    *   `.sh`
    are submitted

*   Only the specified folder is scanned (not subfolders)
*   If no job files are found, the script prints a message

## Safety notes
*   The script submits all matching files, so make sure:
    *   Your job scripts are correct
    *   You do not accidentally submit unwanted jobs

## Make executable (optional)
```bash
chmod +x submit_many_jobs.sh
```

Then run:
```bash
./submit_many_jobs.sh jobs/
```

## Typical use cases
*   Submitting many simulation jobs
*   Running batch ML experiments
*   Launching multiple preprocessing jobs
*   Managing large HPC workflows

