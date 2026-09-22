# gather_files.sh

## Overview

`gather_files.sh` is a general-purpose Bash utility for collecting files from a directory tree into a single location.

It supports pattern-based search, copying/moving files, preserving directory structure, and generating a manifest.

---

## Features

- Pattern-based file selection (`*.npy`, `*.log`, etc.)
- Copy or move files
- Optional overwrite protection
- Preserve folder hierarchy
- Manifest CSV generation
- Works on Linux and macOS

---

## Installation

```bash
chmod +x gather_files.sh
```

## Usage
```bash
./gather_files.sh [options]
```

## Options
| Option                 |	Description                                          |
|------------------------|-------------------------------------------------------|
|`--search-root=PATH`    | Directory to search (default: current directory)      |
|`--output-dir=PATH`	 | Destination directory                                 |
|`--pattern=PATTERN`	 | File pattern (default: `*.npy`)                       |
|`--action=copy/move`    | Action to perform (default: `copy`)                   |
|`--overwrite`	         | Overwrite existing files                              |
|`--preserve-structure`	 | Keep folder hierarchy                                 |
|`--no-manifest`	     | Disable manifest generation                           |

## Examples

### Collect `.npy` files

```bash
./gather_files.sh --pattern="*.npy"
```

### Collect logs and keep structure

```bash
./gather_files.sh --pattern="*.log" --preserve-structure
```
### Move files instead of copying

```bash
./gather_files.sh --action=move
```

### Output Example

```
collected_files/
├── file1.npy
├── file2.npy
└── manifest.csv
```

### Manifest Format

```
filename,bytes,path
file1.npy,123456,/path/to/file1.npy
file2.npy,654321,/path/to/file2.npy
```

## Use Cases
-   Machine learning experiment outputs
-   Simulation results aggregation
-   Log file collection
-   Dataset organization

