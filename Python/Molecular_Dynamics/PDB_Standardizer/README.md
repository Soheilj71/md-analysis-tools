# PDB Standardizer

A Python script to standardize selected records in a PDB file using fixed-width column formatting and strict left/right alignment rules based on the user-defined format tables.

This tool reads a PDB file, rewrites supported records into standardized column-based format, and produces a log file that records every field-level change made during processing.

## Features

- Accepts a PDB file as input
- Standardizes these record types:
  - `ATOM`
  - `HETATM`
  - `TER`
  - `HELIX`
  - `SHEET`
  - `SSBOND`
- Applies fixed-width formatting
- Respects explicit left/right alignment rules for each supported field
- Writes a cleaned output PDB file
- Writes a detailed log file with every field-level change
- Preserves unsupported records unchanged

## Why this tool is useful

PDB files are column-based text files. Many downstream molecular modeling, structural biology, and scripting workflows depend on exact column placement. Even when the scientific content is correct, inconsistent spacing or incorrect alignment can cause problems in parsers, analysis scripts, and simulation pipelines.

This script helps standardize formatting so the file layout is more consistent and easier to validate, inspect, and reuse.

## Supported records

The script currently reformats the following PDB record types:

- `ATOM`
- `HETATM`
- `TER`
- `HELIX`
- `SHEET`
- `SSBOND`

All other record types are passed through unchanged.

## What the script does

For supported records, the script:

1. Reads the fields from their expected column ranges
2. Parses numeric and text values
3. Fixes missing numeric values using defaults when needed
4. Rewrites the record using strict column widths
5. Applies left or right alignment according to the formatting rules
6. Logs every field that changed

## What the script does not do

This script is a formatter, not a structure interpreter.

It does **not**:

- predict missing secondary structure
- detect disulfide bonds from coordinates
- validate chemistry
- renumber atoms or residues intelligently
- correct biologically incorrect annotations
- rebuild missing records from scratch

It only reformats supported records using fixed-width text rules and logs the changes.

## Files in this project

- `pdb_standardize_final.py`  
  Main Python script

## Requirements

- Python 3.8 or newer

No external packages are required.

## Usage

### Basic usage

```bash
python pdb_standardize_final.py input.pdb
```

This creates:

*   `input_standardized.pdb`
*   `input_standardized.log`

## Custom output names
```bash
python pdb_standardize_final.py input.pdb -o cleaned.pdb -l changes.log
```

## Example
### Command
```bash
python pdb_standardize_final.py protein.pdb -o cleaned.pdb -l changes.log
```

### Output

*   `cleaned.pdb` → standardized PDB file
*   `changes.log` → field-level record of all changes

### Example log entries
```
Line 2 [ATOM] atom name changed (13-16, left) | old='  N ' | new='N   '
Line 2 [ATOM] residue sequence number changed (23-26, right) | old='1   ' | new='   1'
Line 15 [ATOM] X coordinate changed (31-38, right) | old='18.88   ' | new='  18.880'
Line 80 [SSBOND] disulfide bond length changed (74-78, right) | old='2.0  ' | new=' 2.00'
```

## Output naming

If you do not provide output names, the script automatically generates them from the input filename.

For example:

Input:
```
protein.pdb
```

Default outputs:

```
protein_standardized.pdb
protein_standardized.log
```

## Alignment rules

This script follows the explicit alignment rules used in the project tables.

Examples:

*   `ATOM` name field may be left-aligned if the table specifies left alignment
*   residue name may be right-aligned
*   coordinate fields are right-aligned
*   segment identifier may be left-aligned

## Important note about PDB conventions

This script follows the alignment rules defined for this project.

That means it may differ from some historical or broader wwPDB formatting conventions, especially in fields such as atom names. If your workflow depends on a different interpretation of the PDB standard, review the output before using it in production pipelines.

## Error handling

*   Unsupported records are preserved exactly as they appear in the input file
*   If a supported record cannot be reformatted safely, the original line is preserved and the issue is written to the log
*   Missing numeric fields may be replaced by default values such as `0`, `0.00`, or `1.00`, depending on the field

## Default values used when needed

Examples of automatic fixes include:
*   missing serial number → `0`
*   missing residue sequence number → `0`
*   missing coordinates → `0.000`
*   missing occupancy → `1.00`
*   missing temperature factor → `0.00`

These fixes are recorded in the log file.

*   Suggested use cases
*   cleaning PDB files before downstream scripting
*   standardizing text layout for internal pipelines
*   debugging column-based parser issues
*   preparing example files for teaching or documentation
*   comparing formatting changes line by line

## Limitations

Only selected record types are standardized
The script does not infer missing structural annotations
The script assumes the input is intended to be a PDB-like fixed-column file

## Author
This script was developed by Soheil Jamali. 
For questions, feedback, or contributions, please contact sjamali@uark.edu and soheil.jamali.dev@gmail.com
