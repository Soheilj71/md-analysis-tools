# Check My SLURM Queue

A simple Bash script to display your SLURM jobs in a clean, compact, and readable format.

This is especially useful for HPC users who frequently monitor running and pending jobs.

---

## What this script does

This script:

1. Queries SLURM using `squeue`
2. Filters jobs by a specific user
3. Displays the results in a formatted table

---

## File

- `check_my_queue.sh`

---

## Usage

```bash
bash check_my_queue.sh
```

or specify a user:

```bash
bash check_my_queue.sh username
```

## Examples

Check your own jobs:
```bash
bash check_my_queue.sh
```
Check another user's jobs:

```bash
bash check_my_queue.sh soheil
```

## Example output
```
SLURM Job Queue for user: soheil
==============================================================
JOBID              PARTITION JOBNAME                       STATE    TIME       NODES NODELIST(REASON)
123456             gpu       train_model                   RUNNING  01:23:45   1     gpu-node01
123457             cpu       analysis_job                  PENDING  00:00:00   1     (Priority)
```

## Column explanation
|Column	           | Meaning                                         |
|------------------|-------------------------------------------------|
|JOBID	           | Unique job identifier                           |
|PARTITION         | Queue/partition used (e.g., gpu, cpu)           |
|JOBNAME           | Name of the job                                 |
|STATE	           | Job status (RUNNING, PENDING, COMPLETED, etc.)  |
|TIME	           | Time the job has been running                   |
|NODES	           | Number of nodes used                            |
|NODELIST / REASON | Node assigned or reason for pending             |

## Requirements
*   SLURM workload manager
*   Access to `squeue` command

Typical environments:
*   HPC clusters (e.g., Delta, Pinnacle, etc.)

## Important notes
*   If no username is provided, the script automatically uses:
```bash
$USER
```
*   If `squeue` is not available, the script will exit with an error.

## Make executable (optional)
```bash
chmod +x check_my_queue.sh
```
Then run:
```bash
./check_my_queue.sh
```

## Customization
You can modify the output format by editing this line:
```bash
squeue -u "${user_name}" -o "FORMAT"
```
For example, to add more details, refer to:
```bash
man squeue
```

## Use case (real HPC workflow)
This script is useful when you:
*   Run multiple jobs on clusters like Delta or Pinnacle
*   Want a quick overview of job status
*   Need a cleaner output than default `squeue`

