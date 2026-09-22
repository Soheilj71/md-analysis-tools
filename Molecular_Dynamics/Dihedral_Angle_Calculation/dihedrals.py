#!/usr/bin/env python3
"""
================================================================================
Universal Dihedral Angle Calculator (Tutorial Version)
================================================================================

This script calculates dihedral angles from molecular dynamics (MD) simulations.

A "dihedral angle" (also called a torsion angle) is defined by FOUR atoms:
  Atom1 - Atom2 - Atom3 - Atom4

The angle describes how Atom1 and Atom4 rotate around the bond between Atom2-Atom3.

This script supports TWO common use cases:

1) Protein backbone angles (automatic):
   - phi   (ϕ)
   - psi   (ψ)
   - omega (ω)
   In this mode, the user does NOT need to provide atoms.
   We assume standard backbone atom names: N, CA, C

2) Custom torsions (user-defined):
   The user can provide any four atoms (by selection strings) to compute any dihedral.
   This is useful for side-chains, ligands, and special torsions.

Inputs:
  - One topology file (structure information)
  - One trajectory file (coordinates for many time frames)

Works for many engines (GROMACS, NAMD, AMBER, CHARMM, etc.) as long as
MDAnalysis can read the files.

Outputs:
  - NPZ (recommended): compact, good for large systems
  - Optional CSV: easy to open in Excel, but can become huge

================================================================================
"""

# ==============================================================================
# 1) Imports: load the Python libraries we need
# ==============================================================================

import argparse
# argparse helps us read command-line arguments like:
#   python script.py -t topol.tpr -x traj.xtc

import numpy as np
# numpy is used for arrays and saving results

import MDAnalysis as mda
# MDAnalysis reads topology/trajectory files from many MD engines

from MDAnalysis.analysis.dihedrals import Dihedral
# Dihedral is a built-in MDAnalysis tool to compute torsion angles


# ==============================================================================
# 2) Small helper functions (tiny reusable pieces)
# ==============================================================================

def radians_to_degrees(angle_in_radians):
    """
    MDAnalysis returns angles in radians.
    Humans usually prefer degrees, so we convert.
    """
    return np.rad2deg(angle_in_radians)


def select_exactly_one_atom(u, selection, label):
    """
    This function finds EXACTLY ONE atom using an MDAnalysis selection string.

    Why do we need this?
    A dihedral must be defined by exactly 4 specific atoms.
    If a selection matches:
      - 0 atoms: you picked something that does not exist
      - >1 atoms: you picked something ambiguous (too broad)

    Parameters:
      u        : MDAnalysis Universe (the simulation)
      selection: selection string (example: "resid 10 and name CA")
      label    : a name used in error messages (helps the user debug)

    Returns:
      a single Atom object

    Raises:
      RuntimeError if the selection does not match exactly 1 atom
    """
    atoms = u.select_atoms(selection)  # MDAnalysis returns an AtomGroup (like a list)

    if len(atoms) != 1:
        raise RuntimeError(
            f"[{label}] Selection must match exactly 1 atom, but matched {len(atoms)}.\n"
            f"Selection: {selection}\n"
            "Tip: Make the selection more specific (add segid, resid, name, etc.)."
        )

    return atoms[0]  # return the only atom


def get_atom_from_residue_or_none(residue, atom_name):
    """
    Try to fetch exactly one atom from a residue by its atom name.
    Example atom names for protein backbone: N, CA, C

    If the atom is missing or not unique, return None instead of crashing.
    This allows the script to skip residues where a backbone atom is missing
    (common at termini or unusual residues).
    """
    group = residue.atoms.select_atoms(f"name {atom_name}")
    if len(group) != 1:
        return None
    return group[0]


# ==============================================================================
# 3) Backbone dihedral building (phi / psi / omega)
# ==============================================================================

def build_backbone_dihedral_quads(residues, N_name="N", CA_name="CA", C_name="C"):
    """
    Build the 4-atom definitions needed to compute phi/psi/omega for a protein chain.

    residues: list of residues IN ORDER along the chain

    Backbone definitions:

      phi (ϕ)   = C(i-1) - N(i)  - CA(i) - C(i)
      psi (ψ)   = N(i)   - CA(i) - C(i)  - N(i+1)
      omega (ω) = CA(i)  - C(i)  - N(i+1) - CA(i+1)

    Not all residues have all these angles:
      - The first residue has no phi (no previous residue)
      - The last residue has no psi (no next residue)
      - Missing atoms -> skip

    Returns:
      phi_quads, psi_quads, omega_quads : lists of quadruplets (each quadruplet = 4 atoms)
      phi_meta,  psi_meta,  omega_meta  : lists describing what each column corresponds to
    """
    phi_quads, psi_quads, omega_quads = [], [], []
    phi_meta, psi_meta, omega_meta = [], [], []

    for i in range(len(residues)):
        r = residues[i]

        # --------------------------
        # PHI (ϕ): needs previous residue
        # --------------------------
        if i - 1 >= 0:
            r_prev = residues[i - 1]

            C_prev = get_atom_from_residue_or_none(r_prev, C_name)
            N = get_atom_from_residue_or_none(r, N_name)
            CA = get_atom_from_residue_or_none(r, CA_name)
            C = get_atom_from_residue_or_none(r, C_name)

            # Only add phi if all required atoms exist
            if all(a is not None for a in [C_prev, N, CA, C]):
                phi_quads.append([C_prev, N, CA, C])
                phi_meta.append((r.segid, r.resid, r.resname))

        # --------------------------
        # PSI (ψ): needs next residue
        # --------------------------
        if i + 1 < len(residues):
            r_next = residues[i + 1]

            N = get_atom_from_residue_or_none(r, N_name)
            CA = get_atom_from_residue_or_none(r, CA_name)
            C = get_atom_from_residue_or_none(r, C_name)
            N_next = get_atom_from_residue_or_none(r_next, N_name)

            if all(a is not None for a in [N, CA, C, N_next]):
                psi_quads.append([N, CA, C, N_next])
                psi_meta.append((r.segid, r.resid, r.resname))

        # --------------------------
        # OMEGA (ω): peptide bond torsion between r and r_next
        # --------------------------
        if i + 1 < len(residues):
            r_next = residues[i + 1]

            CA = get_atom_from_residue_or_none(r, CA_name)
            C = get_atom_from_residue_or_none(r, C_name)
            N_next = get_atom_from_residue_or_none(r_next, N_name)
            CA_next = get_atom_from_residue_or_none(r_next, CA_name)

            if all(a is not None for a in [CA, C, N_next, CA_next]):
                omega_quads.append([CA, C, N_next, CA_next])
                omega_meta.append((r.segid, r.resid, r.resname, r_next.resid, r_next.resname))

    return phi_quads, psi_quads, omega_quads, phi_meta, psi_meta, omega_meta


def compute_dihedrals_for_quads(u, quads):
    """
    Compute dihedral angles for a list of quadruplets over all frames.

    u     : MDAnalysis Universe
    quads : list of [atom1, atom2, atom3, atom4]

    Returns:
      angles_deg with shape (n_frames, n_dihedrals)
    """
    n_frames = len(u.trajectory)

    # If there are no dihedrals to compute, return empty array
    if len(quads) == 0:
        return np.empty((n_frames, 0), dtype=float)

    # Run MDAnalysis dihedral analysis
    # Result is in radians with shape (n_frames, n_dihedrals)
    analysis = Dihedral(quads).run()

    # Convert radians to degrees
    return radians_to_degrees(analysis.angles)


# ==============================================================================
# 4) Custom torsions: user gives 4 atom selections
# ==============================================================================

def parse_torsion_argument(text):
    """
    Parse one --torsion argument from the command line.

    Required format:
      "NAME: SEL1 | SEL2 | SEL3 | SEL4"

    Example:
      --torsion "chi1_res10: (resid 10 and name N) | (resid 10 and name CA) | (resid 10 and name CB) | (resid 10 and name CG)"

    Returns:
      name (string), selections (list of 4 selection strings)
    """
    if ":" not in text:
        raise ValueError("Torsion format must include ':' to separate name and selections.")

    name, right = text.split(":", 1)
    name = name.strip()

    selections = [p.strip() for p in right.split("|")]

    if len(selections) != 4:
        raise ValueError("Torsion must have 4 selections separated by '|'.")

    return name, selections


# ==============================================================================
# 5) Saving CSV (optional)
# ==============================================================================

def save_csv_wide(csv_path, times, columns, headers):
    """
    Save a CSV in "wide" format:
      time, col1, col2, col3, ...

    This is easy for Excel, but can become huge.
    Use NPZ for large systems.
    """
    data = np.column_stack([times] + columns)
    header_line = ",".join(["time"] + headers)
    np.savetxt(csv_path, data, delimiter=",", header=header_line, comments="")
    print(f"Saved CSV: {csv_path}")


# ==============================================================================
# 6) Main program: reading inputs, running calculations, saving outputs
# ==============================================================================

def main():
    # --------------------------------------------------------------------------
    # A) Define command-line arguments (what users type when running the script)
    # --------------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Universal dihedral calculator: backbone phi/psi/omega + custom torsions."
    )

    # Topology and trajectory are required
    parser.add_argument("-t", "--top", required=True, help="Topology file (TPR/PSF/PRMTOP/PDB/...).")
    parser.add_argument("-x", "--traj", required=True, help="Trajectory file (XTC/DCD/TRR/NC/...).")

    # Output options
    parser.add_argument("-o", "--out", default="dihedrals_output.npz", help="Output NPZ filename.")
    parser.add_argument("--csv", default=None, help="Optional CSV filename (wide format).")

    # Backbone mode options
    parser.add_argument("-s", "--selection", default="protein",
                        help="Selection for the protein (default: protein).")
    parser.add_argument("--no-backbone", action="store_true",
                        help="Disable backbone phi/psi/omega calculation.")

    # Atom name overrides (rarely needed)
    parser.add_argument("--N-name", default="N", help="Backbone N atom name (default: N).")
    parser.add_argument("--CA-name", default="CA", help="Backbone CA atom name (default: CA).")
    parser.add_argument("--C-name", default="C", help="Backbone C atom name (default: C).")

    # Custom torsions can be provided multiple times
    parser.add_argument("--torsion", action="append", default=[],
                        help="Custom dihedral: \"NAME: SEL1 | SEL2 | SEL3 | SEL4\" (repeatable).")

    args = parser.parse_args()

    # --------------------------------------------------------------------------
    # B) Load the simulation into an MDAnalysis Universe
    # --------------------------------------------------------------------------
    # Universe = topology + trajectory
    u = mda.Universe(args.top, args.traj)

    # --------------------------------------------------------------------------
    # C) Collect time for each frame
    # --------------------------------------------------------------------------
    # Many trajectories store time information. If not, time may be 0 for all frames.
    times = np.array([ts.time for ts in u.trajectory], dtype=float)

    # We moved through the trajectory to read times, so we rewind for analyses.
    u.trajectory.rewind()

    # --------------------------------------------------------------------------
    # D) Prepare containers to store results
    # --------------------------------------------------------------------------
    results = {
        "time": times,
        "topology": args.top,
        "trajectory": args.traj,
    }

    # For CSV output (optional)
    csv_columns = []
    csv_headers = []

    # --------------------------------------------------------------------------
    # E) Backbone calculation (phi/psi/omega)
    # --------------------------------------------------------------------------
    if not args.no_backbone:
        # Select protein atoms using the user-provided selection string
        prot = u.select_atoms(args.selection)

        if len(prot) == 0:
            raise RuntimeError(
                f"Selection '{args.selection}' matched 0 atoms.\n"
                "Try a different selection (example: 'protein', 'segid A', etc.)."
            )

        # We split residues by segid (similar to chains in many systems)
        segids = sorted(set(prot.residues.segids))

        all_phi_quads, all_psi_quads, all_omega_quads = [], [], []
        all_phi_meta, all_psi_meta, all_omega_meta = [], [], []

        for segid in segids:
            # Pick residues in this segid
            seg_res = prot.residues[prot.residues.segids == segid]

            # Sort residues by resid so "neighbors" are correct
            seg_res = sorted(seg_res, key=lambda r: r.resid)

            # Build atom quadruplets for backbone angles
            phi_q, psi_q, omega_q, phi_m, psi_m, omega_m = build_backbone_dihedral_quads(
                seg_res,
                N_name=args.N_name,
                CA_name=args.CA_name,
                C_name=args.C_name,
            )

            all_phi_quads.extend(phi_q)
            all_psi_quads.extend(psi_q)
            all_omega_quads.extend(omega_q)
            all_phi_meta.extend(phi_m)
            all_psi_meta.extend(psi_m)
            all_omega_meta.extend(omega_m)

        # Compute angles (degrees) over all frames
        phi_deg = compute_dihedrals_for_quads(u, all_phi_quads)
        psi_deg = compute_dihedrals_for_quads(u, all_psi_quads)
        omega_deg = compute_dihedrals_for_quads(u, all_omega_quads)

        # Save into NPZ results
        results["phi_deg"] = phi_deg
        results["psi_deg"] = psi_deg
        results["omega_deg"] = omega_deg
        results["phi_meta"] = np.array(all_phi_meta, dtype=object)
        results["psi_meta"] = np.array(all_psi_meta, dtype=object)
        results["omega_meta"] = np.array(all_omega_meta, dtype=object)
        results["selection"] = args.selection

        # Add backbone angles to CSV columns (optional)
        # phi_deg has shape (n_frames, n_phi)
        for (segid, resid, resname), col in zip(all_phi_meta, phi_deg.T):
            csv_columns.append(col)
            csv_headers.append(f"phi_{segid}:{resid}:{resname}")

        for (segid, resid, resname), col in zip(all_psi_meta, psi_deg.T):
            csv_columns.append(col)
            csv_headers.append(f"psi_{segid}:{resid}:{resname}")

        for (segid, resid, resname, resid2, resname2), col in zip(all_omega_meta, omega_deg.T):
            csv_columns.append(col)
            csv_headers.append(f"omega_{segid}:{resid}:{resname}->{resid2}:{resname2}")

        print("Backbone dihedrals done.")
        print(f"  phi columns:   {phi_deg.shape[1]}")
        print(f"  psi columns:   {psi_deg.shape[1]}")
        print(f"  omega columns: {omega_deg.shape[1]}")

    # --------------------------------------------------------------------------
    # F) Custom torsions calculation
    # --------------------------------------------------------------------------
    if args.torsion:
        torsion_names = []
        torsion_arrays = []

        for torsion_text in args.torsion:
            # Convert text into (name, [sel1, sel2, sel3, sel4])
            name, sels = parse_torsion_argument(torsion_text)

            # Convert selections into EXACT atom objects
            a1 = select_exactly_one_atom(u, sels[0], f"{name}:atom1")
            a2 = select_exactly_one_atom(u, sels[1], f"{name}:atom2")
            a3 = select_exactly_one_atom(u, sels[2], f"{name}:atom3")
            a4 = select_exactly_one_atom(u, sels[3], f"{name}:atom4")

            # Compute the dihedral for this torsion across all frames
            # We pass a list with ONE quadruplet
            angles_deg = compute_dihedrals_for_quads(u, [[a1, a2, a3, a4]])
            angles_deg = angles_deg[:, 0]  # shape becomes (n_frames,)

            torsion_names.append(name)
            torsion_arrays.append(angles_deg)

            # Add to CSV output (optional)
            csv_columns.append(angles_deg)
            csv_headers.append(f"torsion_{name}")

            print(f"Custom torsion done: {name}")

        # Save custom torsions into NPZ
        results["custom_torsion_names"] = np.array(torsion_names, dtype=object)
        results["custom_torsion_deg"] = np.column_stack(torsion_arrays)

    # --------------------------------------------------------------------------
    # G) Save NPZ results (recommended)
    # --------------------------------------------------------------------------
    np.savez(args.out, **results)
    print(f"\nSaved NPZ: {args.out}")
    print(f"Frames: {len(times)}")

    # --------------------------------------------------------------------------
    # H) Save CSV results (optional)
    # --------------------------------------------------------------------------
    if args.csv is not None:
        if len(csv_columns) == 0:
            raise RuntimeError(
                "You asked for --csv, but no dihedrals were computed.\n"
                "Either remove --csv, or compute backbone/custom torsions."
            )
        save_csv_wide(args.csv, times, csv_columns, csv_headers)


# ==============================================================================
# 7) Python “entry point”
# ==============================================================================
# This is a standard Python pattern:
# - If you run this file directly: it executes main()
# - If you import this file as a library: it does NOT auto-run
if __name__ == "__main__":
    main()
