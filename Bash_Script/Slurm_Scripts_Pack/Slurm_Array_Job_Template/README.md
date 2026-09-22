# SLURM Array Job Template

A generic Bash template for running many similar jobs on HPC systems that use the **SLURM** scheduler.

This repository provides a simple example of how to use a **job array**, where one script is launched many times and each task works on a different input.

---

## What is a SLURM array job?

A SLURM array job lets you submit many related jobs at once using a single submission script.

Instead of manually submitting many separate jobs, you submit one script like this:

```bash
sbatch slurm_array_job_template.sh
```
SLURM then runs multiple tasks from that one script.

Each task gets its own array index:
```bash
SLURM_ARRAY_TASK_ID
```
That index is used to select one input item from a list.

## Core idea
You have:
*   one script
*   many inputs
*   one task per input

For example:

|Task ID	|  Input file  |
|-----------|--------------|
|0	        | input_0.txt  |
|1	        | input_1.txt  |
|2	        | input_2.txt  |
|...        |	...        |
|9	        | input_9.txt  |

So the same workflow runs multiple times, but each task uses a different input.

## File

*   `slurm_array_job_template.sh`

## Important note about portability
This script is written as a generic example for HPC systems that use SLURM.

However, every HPC cluster is different. Items such as these may need to be changed:

*   partition/queue name
*   account/allocation name
*   memory limits
*   CPU settings
*   wall time limits
*   log file policies

So the `#SBATCH` lines in this script should be treated as examples unless they match your HPC system exactly.

Always check your cluster documentation.

## How it works
The script does the following:

*   Requests resources from SLURM
*   Creates a `logs`/ folder
*   Defines a Bash array of input items
*   Uses `SLURM_ARRAY_TASK_ID` to choose one input
*   Runs the same workflow on that input

The key line is:
```bash
current_input="${inputs[$SLURM_ARRAY_TASK_ID]}"
```

This means:
*   task 0 gets the first input
*   task 1 gets the second input
*   task 2 gets the third input
*   and so on

## Example SLURM settings

Inside the script you will see lines like:
```bash
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --partition=compute
#SBATCH --array=0-9
```

These are only example settings.

You should replace them with values appropriate for your own HPC system and workload.

## Usage

Submit the script with:

```bash
sbatch slurm_array_job_template.sh
```

## Example input list

The template includes this example:
```bash
inputs=(
    input_0.txt
    input_1.txt
    input_2.txt
    input_3.txt
    input_4.txt
    input_5.txt
    input_6.txt
    input_7.txt
    input_8.txt
    input_9.txt
)
```

The array range is:
```bash
#SBATCH --array=0-9
```

That means there are 10 tasks total, and each task uses one input.

## Very important rule
The number of tasks in `--array` must match the number of inputs.

Example:
*   10 inputs
*   array should be `0-9`

If you have 20 inputs, change it to:
```bash
#SBATCH --array=0-19
```

## Example command

The template currently uses a placeholder command:
```bash
echo "Pretend processing ${current_input}"
```

Replace that with your real workflow.

For example:
```bash
python process_one_file.py --input "${current_input}"
```

or
```bash
bash run_simulation.sh "${current_input}"
```

or
```bash
gmx mdrun -s "${current_input}"
```
depending on your application.

## Example output logs

The script writes logs using:
```bash
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err
```

This helps keep output from each array task separate.

Meaning of placeholders:
*   `%x` = job name
*   `%A` = main array job ID
*   `%a` = array task ID

Example output files:
```
logs/array_job_123456_0.out
logs/array_job_123456_1.out
logs/array_job_123456_2.out
```

## Typical use cases

SLURM job arrays are useful for:
*   processing many files
*   running one simulation per system
*   running many independent MD jobs
*   evaluating multiple datasets
*   sweeping hyperparameters
*   training multiple models with different settings
*   performing repeated analyses

## Example: process many files

Suppose you have 10 input files and want one task per file.

You define:
```bash
inputs=(
    file_0.dat
    file_1.dat
    file_2.dat
    file_3.dat
    file_4.dat
    file_5.dat
    file_6.dat
    file_7.dat
    file_8.dat
    file_9.dat
)
```

and:
```bash
#SBATCH --array=0-9
```

Then each task processes one file.

## Example: one script, many runs
This is the main concept:
*   one submission file
*   same workflow command
*   different input for each task

So it is like running this many times:
```
task 0 → run workflow on input 0
task 1 → run workflow on input 1
task 2 → run workflow on input 2
...
```

but SLURM manages it for you.

## Make executable (optional)
```bash
chmod +x slurm_array_job_template.sh
```

Then submit with:
```bash
sbatch slurm_array_job_template.sh
```

## Before submitting on your HPC
Check these items:
*   Does your cluster use SLURM?
*   Is the partition name valid?
*   Do you need an account line?
*   Are the requested time and memory acceptable?
*   Does the array range match your number of inputs?
*   Did you replace the example command with your real command?

