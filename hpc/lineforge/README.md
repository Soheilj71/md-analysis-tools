# 🔧 lineforge

> A safe, flexible, and production-ready CLI tool for batch line replacement across files.

---

## 🚀 Overview

`lineforge` is a Bash-based utility designed to simplify and standardize line replacement across large collections of files.

While Linux provides powerful tools like `sed`, `awk`, and `find`, combining them for real-world workflows can quickly become complex, error-prone, and difficult to reuse.

`lineforge` provides a **clean, safe, and reproducible interface** for these operations.

---

## ✨ Features

- 🔍 Multiple matching modes:
  - `exact` → match full line exactly  
  - `contains` → match substring  
  - `regex` → full pattern matching  

- 🛡️ Safe execution:
  - `--dry-run` (preview changes before applying)
  - automatic backups (`.bak` or custom)

- 🎯 Fine control:
  - replace first match (default)
  - or replace all matches (`--all`)

- 📂 Flexible file targeting:
  - directory glob mode
  - recursive search mode

- ⚡ Efficient:
  - skips files with no changes
  - avoids unnecessary rewrites

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/your-username/lineforge.git
cd lineforge
chmod +x change_any_line.sh
```
(Optional) Move to your PATH:
```bash
mv change_any_line.sh /usr/local/bin/lineforge
```

## 🧪 Quick Examples

### 1. Exact match replacement

```bash
lineforge \
  --search "#SBATCH --time=72:00:00" \
  --to "#SBATCH --time=48:00:00" \
  --glob "max_*" \
  --file "src/slurm.sh"
```

### 2. Regex replacement across all `.sh` files

```bash
lineforge \
  --mode regex \
  --search '^#SBATCH[[:space:]]+--time=.*$' \
  --to '#SBATCH --time=48:00:00' \
  --root . \
  --name '*.sh'
```

### 3. Dry-run (preview changes)

```bash
lineforge \
  --search "OLD_LINE" \
  --to "NEW_LINE" \
  --root . \
  --name "*.txt" \
  --dry-run
```

### 4. Replace all matches

```bash
lineforge \
  --search "module load old" \
  --to "module load new" \
  --root . \
  --name "*.sh" \
  --all
```

## ⚖️ Comparison with Built-in Linux Tools

Linux already provides powerful text-processing utilities such as:

*   `sed`
*   `awk`
*   `grep`
*   `find`

However, these tools operate at a low level and require manual composition for complex workflows.

## 🔹 Example using native tools
```bash
find . -name "*.sh" -exec sed -i 's/OLD/NEW/' {} +
```

## ❗ Limitations of built-in tools

| Limitation	                | Description                       |
|-------------------------------|-----------------------------------|
| ❌ No dry-run                 | Changes are applied immediately   |
| ❌ No automatic backups    	| Risk of data loss                 |
| ❌ Limited control            | Hard to restrict to first match   |
| ❌ Hard to reuse              | Commands are not structured       |
| ❌ Poor readability	        | Complex one-liners                |
| ❌ Error-prone	            | Easy to make mistakes at scale    |

## ✅ What `lineforge` solves

| Feature            | Built-in Tools            	|  `lineforge`                 |
|--------------------|------------------------------|------------------------------|
| Matching modes	 | Partial	                    | ✔ exact / contains / regex   |
| Dry-run support	 | ❌	                        | ✔                            |
| Automatic backup 	 | ❌	                        | ✔                            |
| Replace control	 | Limited	                    | ✔ first / all                |
| File selection   	 | Manual	                    | ✔ structured                 |
| Safety	         | Low	                        | ✔ high                       |
| Reusability	     | Low	                        | ✔ high                       |
| Readability	     | Low	                        | ✔ high                       |

## 🧠 Conceptual Difference

*   **Linux tools** → low-level building blocks
*   **lineforge** → high-level workflow tool

`lineforge` does not replace `sed` or `awk` — it engineers them into a safe, reusable system.

## 🎯 When to Use lineforge

Use this tool when:
*   You need to modify many files across directories
*   You want safe and reversible changes
*   You are working in HPC / batch workflows (e.g., SLURM)
*   You want clean, repeatable automation

## 📁 Use Cases
*   Updating SLURM job scripts across experiments
*   Refactoring configuration files
*   Standardizing headers across datasets
*   Large-scale codebase edits

## ⚠️ Notes
*   Always use `--dry-run` before large changes
*   Backups are enabled by default (`.bak`)
*   Use regex mode carefully for complex patterns

## 🤝 Contributing
Feel free to submit issues or improvements.

