#!/usr/bin/env python3
"""
pdb_standardize_final.py

Strict PDB formatter with field-level logging.

Supported records:
- ATOM
- HETATM
- TER
- HELIX
- SHEET
- SSBOND

The log file records every field that changed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# ============================================================
# Basic helpers
# ============================================================

def safe_slice(text: str, start_1based: int, end_1based: int) -> str:
    """Return substring using 1-based inclusive column indexing."""
    start = max(0, start_1based - 1)
    end = max(start, end_1based)
    return text[start:end]


def parse_int(text: str) -> Optional[int]:
    text = text.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_float(text: str) -> Optional[float]:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def left(text: str, width: int) -> str:
    """Left-justify text into fixed width."""
    return str(text).strip()[:width].ljust(width)


def right(text: str, width: int) -> str:
    """Right-justify text into fixed width."""
    return str(text).strip()[:width].rjust(width)


def int_field(value: Optional[int], width: int, default: int = 0) -> str:
    if value is None:
        value = default
    return right(str(value), width)


def float_field(value: Optional[float], width: int, decimals: int, default: float = 0.0) -> str:
    if value is None:
        value = default
    return right(f"{value:.{decimals}f}", width)


def add_change(log_messages: List[str], line_no: int, record_type: str, message: str) -> None:
    log_messages.append(f"Line {line_no} [{record_type}] {message}")


def compare_field(
    original: str,
    new: str,
    line_no: int,
    record_type: str,
    field_name: str,
    columns: str,
    justification: str,
    log_messages: List[str],
) -> None:
    if original != new:
        add_change(
            log_messages,
            line_no,
            record_type,
            f"{field_name} changed ({columns}, {justification}) | old='{original}' | new='{new}'"
        )


def guess_element_from_atom_name(atom_name: str) -> str:
    """Best-effort guess of element if element field is empty."""
    name = atom_name.strip()
    if not name:
        return ""

    if name[0].isdigit():
        name = name[1:]

    letters = "".join(ch for ch in name if ch.isalpha())
    if not letters:
        return ""

    two_letter = {
        "FE", "ZN", "MG", "CA", "NA", "CL", "BR", "CU", "MN", "CO",
        "NI", "HG", "CD", "AG", "AL", "SI", "LI", "PB", "PT", "AU",
        "SR", "CS", "BA", "RB", "CR", "IR", "OS", "PD", "RH", "RU"
    }

    if len(letters) >= 2 and letters[:2].upper() in two_letter:
        return letters[:2].capitalize()

    return letters[0].upper()


# ============================================================
# Record formatters
# ============================================================

def format_atom_like(record: str, line: str, line_no: int, log_messages: List[str]) -> str:
    # Original slices
    rec_o = safe_slice(line, 1, 6)
    serial_o = safe_slice(line, 7, 11)
    atom_name_o = safe_slice(line, 13, 16)
    altloc_o = safe_slice(line, 17, 17)
    resname_o = safe_slice(line, 18, 20)
    chain_o = safe_slice(line, 22, 22)
    resseq_o = safe_slice(line, 23, 26)
    icode_o = safe_slice(line, 27, 27)
    x_o = safe_slice(line, 31, 38)
    y_o = safe_slice(line, 39, 46)
    z_o = safe_slice(line, 47, 54)
    occ_o = safe_slice(line, 55, 60)
    temp_o = safe_slice(line, 61, 66)
    segid_o = safe_slice(line, 73, 76)
    element_o = safe_slice(line, 77, 78)
    charge_o = safe_slice(line, 79, 80)

    # Parsed values
    serial = parse_int(serial_o)
    atom_name = atom_name_o.strip()
    altloc = altloc_o.strip()
    resname = resname_o.strip()
    chain = chain_o.strip()
    resseq = parse_int(resseq_o)
    icode = icode_o.strip()
    x = parse_float(x_o)
    y = parse_float(y_o)
    z = parse_float(z_o)
    occ = parse_float(occ_o)
    temp = parse_float(temp_o)
    segid = segid_o.strip()
    element = element_o.strip()
    charge = charge_o.strip()

    # Fix missing values
    if serial is None:
        serial = 0
        add_change(log_messages, line_no, record, "serial fixed -> 0")

    if resseq is None:
        resseq = 0
        add_change(log_messages, line_no, record, "residue sequence fixed -> 0")

    if x is None:
        x = 0.0
        add_change(log_messages, line_no, record, "X coordinate fixed -> 0.000")

    if y is None:
        y = 0.0
        add_change(log_messages, line_no, record, "Y coordinate fixed -> 0.000")

    if z is None:
        z = 0.0
        add_change(log_messages, line_no, record, "Z coordinate fixed -> 0.000")

    if occ is None:
        occ = 1.00
        add_change(log_messages, line_no, record, "occupancy fixed -> 1.00")

    if temp is None:
        temp = 0.00
        add_change(log_messages, line_no, record, "temperature factor fixed -> 0.00")

    if not element and atom_name:
        guessed = guess_element_from_atom_name(atom_name)
        if guessed:
            element = guessed
            add_change(log_messages, line_no, record, f"element inferred -> {guessed}")

    # New formatted fields based on your table
    rec_n = left(record, 6)
    serial_n = int_field(serial, 5)
    atom_name_n = left(atom_name, 4)     # left per your table
    altloc_n = left(altloc, 1)
    resname_n = right(resname, 3)        # right
    chain_n = left(chain, 1)
    resseq_n = int_field(resseq, 4)      # right
    icode_n = left(icode, 1)
    x_n = float_field(x, 8, 3)
    y_n = float_field(y, 8, 3)
    z_n = float_field(z, 8, 3)
    occ_n = float_field(occ, 6, 2, default=1.00)
    temp_n = float_field(temp, 6, 2, default=0.00)
    segid_n = left(segid, 4)             # left
    element_n = right(element, 2)        # right
    charge_n = left(charge, 2)

    # Field-level log
    compare_field(rec_o, rec_n, line_no, record, "record type", "1-6", "left", log_messages)
    compare_field(serial_o, serial_n, line_no, record, "serial", "7-11", "right", log_messages)
    compare_field(atom_name_o, atom_name_n, line_no, record, "atom name", "13-16", "left", log_messages)
    compare_field(altloc_o, altloc_n, line_no, record, "alternate location", "17", "left", log_messages)
    compare_field(resname_o, resname_n, line_no, record, "residue name", "18-20", "right", log_messages)
    compare_field(chain_o, chain_n, line_no, record, "chain identifier", "22", "left", log_messages)
    compare_field(resseq_o, resseq_n, line_no, record, "residue sequence number", "23-26", "right", log_messages)
    compare_field(icode_o, icode_n, line_no, record, "insertion code", "27", "left", log_messages)
    compare_field(x_o, x_n, line_no, record, "X coordinate", "31-38", "right", log_messages)
    compare_field(y_o, y_n, line_no, record, "Y coordinate", "39-46", "right", log_messages)
    compare_field(z_o, z_n, line_no, record, "Z coordinate", "47-54", "right", log_messages)
    compare_field(occ_o, occ_n, line_no, record, "occupancy", "55-60", "right", log_messages)
    compare_field(temp_o, temp_n, line_no, record, "temperature factor", "61-66", "right", log_messages)
    compare_field(segid_o, segid_n, line_no, record, "segment identifier", "73-76", "left", log_messages)
    compare_field(element_o, element_n, line_no, record, "element symbol", "77-78", "right", log_messages)
    compare_field(charge_o, charge_n, line_no, record, "charge", "79-80", "left", log_messages)

    newline = (
        rec_n
        + serial_n
        + " "
        + atom_name_n
        + altloc_n
        + resname_n
        + " "
        + chain_n
        + resseq_n
        + icode_n
        + "   "
        + x_n
        + y_n
        + z_n
        + occ_n
        + temp_n
        + "      "
        + segid_n
        + element_n
        + charge_n
    )
    return newline + "\n"


def format_ter(line: str, line_no: int, log_messages: List[str]) -> str:
    rec_o = safe_slice(line, 1, 6)
    serial_o = safe_slice(line, 7, 11)
    resname_o = safe_slice(line, 18, 20)
    chain_o = safe_slice(line, 22, 22)
    resseq_o = safe_slice(line, 23, 26)
    icode_o = safe_slice(line, 27, 27)

    serial = parse_int(serial_o)
    resname = resname_o.strip()
    chain = chain_o.strip()
    resseq = parse_int(resseq_o)
    icode = icode_o.strip()

    if serial is None:
        serial = 0
        add_change(log_messages, line_no, "TER", "serial fixed -> 0")
    if resseq is None:
        resseq = 0
        add_change(log_messages, line_no, "TER", "residue sequence fixed -> 0")

    rec_n = left("TER", 6)
    serial_n = int_field(serial, 5)
    resname_n = right(resname, 3)
    chain_n = left(chain, 1)
    resseq_n = int_field(resseq, 4)
    icode_n = left(icode, 1)

    compare_field(rec_o, rec_n, line_no, "TER", "record type", "1-6", "left", log_messages)
    compare_field(serial_o, serial_n, line_no, "TER", "serial", "7-11", "right", log_messages)
    compare_field(resname_o, resname_n, line_no, "TER", "residue name", "18-20", "right", log_messages)
    compare_field(chain_o, chain_n, line_no, "TER", "chain identifier", "22", "left", log_messages)
    compare_field(resseq_o, resseq_n, line_no, "TER", "residue sequence number", "23-26", "right", log_messages)
    compare_field(icode_o, icode_n, line_no, "TER", "insertion code", "27", "left", log_messages)

    newline = (
        rec_n
        + serial_n
        + "      "
        + resname_n
        + " "
        + chain_n
        + resseq_n
        + icode_n
    )
    return newline + "\n"


def format_helix(line: str, line_no: int, log_messages: List[str]) -> str:
    rec_o = safe_slice(line, 1, 6)
    ser_o = safe_slice(line, 8, 10)
    helix_id_o = safe_slice(line, 12, 14)
    init_res_o = safe_slice(line, 16, 18)
    init_chain_o = safe_slice(line, 20, 20)
    init_seq_o = safe_slice(line, 22, 25)
    init_icode_o = safe_slice(line, 26, 26)
    end_res_o = safe_slice(line, 28, 30)
    end_chain_o = safe_slice(line, 32, 32)
    end_seq_o = safe_slice(line, 34, 37)
    end_icode_o = safe_slice(line, 38, 38)
    helix_class_o = safe_slice(line, 39, 40)
    comment_o = safe_slice(line, 41, 70)
    length_o = safe_slice(line, 72, 76)

    ser = parse_int(ser_o)
    helix_id = helix_id_o.strip()
    init_res = init_res_o.strip()
    init_chain = init_chain_o.strip()
    init_seq = parse_int(init_seq_o)
    init_icode = init_icode_o.strip()
    end_res = end_res_o.strip()
    end_chain = end_chain_o.strip()
    end_seq = parse_int(end_seq_o)
    end_icode = end_icode_o.strip()
    helix_class = parse_int(helix_class_o)
    comment = comment_o.strip()
    length = parse_int(length_o)

    if ser is None:
        ser = 0
        add_change(log_messages, line_no, "HELIX", "serial fixed -> 0")
    if init_seq is None:
        init_seq = 0
        add_change(log_messages, line_no, "HELIX", "initial residue sequence fixed -> 0")
    if end_seq is None:
        end_seq = 0
        add_change(log_messages, line_no, "HELIX", "terminal residue sequence fixed -> 0")
    if helix_class is None:
        helix_class = 0
        add_change(log_messages, line_no, "HELIX", "helix class fixed -> 0")
    if length is None:
        length = 0
        add_change(log_messages, line_no, "HELIX", "helix length fixed -> 0")

    rec_n = left("HELIX", 6)
    ser_n = int_field(ser, 3)
    helix_id_n = right(helix_id, 3)
    init_res_n = right(init_res, 3)
    init_chain_n = left(init_chain, 1)
    init_seq_n = int_field(init_seq, 4)
    init_icode_n = left(init_icode, 1)
    end_res_n = right(end_res, 3)
    end_chain_n = left(end_chain, 1)
    end_seq_n = int_field(end_seq, 4)
    end_icode_n = left(end_icode, 1)
    helix_class_n = int_field(helix_class, 2)
    comment_n = left(comment, 30)
    length_n = int_field(length, 5)

    compare_field(rec_o, rec_n, line_no, "HELIX", "record type", "1-6", "left", log_messages)
    compare_field(ser_o, ser_n, line_no, "HELIX", "helix serial number", "8-10", "right", log_messages)
    compare_field(helix_id_o, helix_id_n, line_no, "HELIX", "helix identifier", "12-14", "right", log_messages)
    compare_field(init_res_o, init_res_n, line_no, "HELIX", "initial residue name", "16-18", "right", log_messages)
    compare_field(init_chain_o, init_chain_n, line_no, "HELIX", "initial chain identifier", "20", "left", log_messages)
    compare_field(init_seq_o, init_seq_n, line_no, "HELIX", "initial residue sequence number", "22-25", "right", log_messages)
    compare_field(init_icode_o, init_icode_n, line_no, "HELIX", "initial insertion code", "26", "left", log_messages)
    compare_field(end_res_o, end_res_n, line_no, "HELIX", "terminal residue name", "28-30", "right", log_messages)
    compare_field(end_chain_o, end_chain_n, line_no, "HELIX", "terminal chain identifier", "32", "left", log_messages)
    compare_field(end_seq_o, end_seq_n, line_no, "HELIX", "terminal residue sequence number", "34-37", "right", log_messages)
    compare_field(end_icode_o, end_icode_n, line_no, "HELIX", "terminal insertion code", "38", "left", log_messages)
    compare_field(helix_class_o, helix_class_n, line_no, "HELIX", "helix type", "39-40", "right", log_messages)
    compare_field(comment_o, comment_n, line_no, "HELIX", "comment", "41-70", "left", log_messages)
    compare_field(length_o, length_n, line_no, "HELIX", "helix length", "72-76", "right", log_messages)

    newline = (
        rec_n
        + " "
        + ser_n
        + " "
        + helix_id_n
        + " "
        + init_res_n
        + " "
        + init_chain_n
        + " "
        + init_seq_n
        + init_icode_n
        + " "
        + end_res_n
        + " "
        + end_chain_n
        + " "
        + end_seq_n
        + end_icode_n
        + helix_class_n
        + comment_n
        + " "
        + length_n
    )
    return newline + "\n"


def format_sheet(line: str, line_no: int, log_messages: List[str]) -> str:
    rec_o = safe_slice(line, 1, 6)
    strand_o = safe_slice(line, 8, 10)
    sheet_id_o = safe_slice(line, 12, 14)
    nstrands_o = safe_slice(line, 15, 16)
    init_res_o = safe_slice(line, 18, 20)
    init_chain_o = safe_slice(line, 22, 22)
    init_seq_o = safe_slice(line, 23, 26)
    init_icode_o = safe_slice(line, 27, 27)
    end_res_o = safe_slice(line, 29, 31)
    end_chain_o = safe_slice(line, 33, 33)
    end_seq_o = safe_slice(line, 34, 37)
    end_icode_o = safe_slice(line, 38, 38)
    sense_o = safe_slice(line, 39, 40)
    cur_atom_o = safe_slice(line, 42, 45)
    cur_res_o = safe_slice(line, 46, 48)
    cur_chain_o = safe_slice(line, 50, 50)
    cur_seq_o = safe_slice(line, 51, 54)
    cur_icode_o = safe_slice(line, 55, 55)
    prev_atom_o = safe_slice(line, 57, 60)
    prev_res_o = safe_slice(line, 61, 63)
    prev_chain_o = safe_slice(line, 65, 65)
    prev_seq_o = safe_slice(line, 66, 69)
    prev_icode_o = safe_slice(line, 70, 70)

    strand = parse_int(strand_o)
    sheet_id = sheet_id_o.strip()
    nstrands = parse_int(nstrands_o)
    init_res = init_res_o.strip()
    init_chain = init_chain_o.strip()
    init_seq = parse_int(init_seq_o)
    init_icode = init_icode_o.strip()
    end_res = end_res_o.strip()
    end_chain = end_chain_o.strip()
    end_seq = parse_int(end_seq_o)
    end_icode = end_icode_o.strip()
    sense = parse_int(sense_o)
    cur_atom = cur_atom_o.strip()
    cur_res = cur_res_o.strip()
    cur_chain = cur_chain_o.strip()
    cur_seq = parse_int(cur_seq_o)
    cur_icode = cur_icode_o.strip()
    prev_atom = prev_atom_o.strip()
    prev_res = prev_res_o.strip()
    prev_chain = prev_chain_o.strip()
    prev_seq = parse_int(prev_seq_o)
    prev_icode = prev_icode_o.strip()

    if strand is None:
        strand = 0
        add_change(log_messages, line_no, "SHEET", "strand number fixed -> 0")
    if nstrands is None:
        nstrands = 0
        add_change(log_messages, line_no, "SHEET", "number of strands fixed -> 0")
    if init_seq is None:
        init_seq = 0
        add_change(log_messages, line_no, "SHEET", "initial residue sequence fixed -> 0")
    if end_seq is None:
        end_seq = 0
        add_change(log_messages, line_no, "SHEET", "terminal residue sequence fixed -> 0")
    if sense is None:
        sense = 0
        add_change(log_messages, line_no, "SHEET", "strand sense fixed -> 0")

    rec_n = left("SHEET", 6)
    strand_n = int_field(strand, 3)
    sheet_id_n = right(sheet_id, 3)
    nstrands_n = int_field(nstrands, 2)
    init_res_n = right(init_res, 3)
    init_chain_n = left(init_chain, 1)
    init_seq_n = int_field(init_seq, 4)
    init_icode_n = left(init_icode, 1)
    end_res_n = right(end_res, 3)
    end_chain_n = left(end_chain, 1)
    end_seq_n = int_field(end_seq, 4)
    end_icode_n = left(end_icode, 1)
    sense_n = int_field(sense, 2)
    cur_atom_n = left(cur_atom, 4)
    cur_res_n = right(cur_res, 3)
    cur_chain_n = left(cur_chain, 1)
    cur_seq_n = int_field(cur_seq, 4) if cur_seq is not None else "    "
    cur_icode_n = left(cur_icode, 1)
    prev_atom_n = left(prev_atom, 4)
    prev_res_n = right(prev_res, 3)
    prev_chain_n = left(prev_chain, 1)
    prev_seq_n = int_field(prev_seq, 4) if prev_seq is not None else "    "
    prev_icode_n = left(prev_icode, 1)

    compare_field(rec_o, rec_n, line_no, "SHEET", "record type", "1-6", "left", log_messages)
    compare_field(strand_o, strand_n, line_no, "SHEET", "strand number", "8-10", "right", log_messages)
    compare_field(sheet_id_o, sheet_id_n, line_no, "SHEET", "sheet identifier", "12-14", "right", log_messages)
    compare_field(nstrands_o, nstrands_n, line_no, "SHEET", "number of strands", "15-16", "right", log_messages)
    compare_field(init_res_o, init_res_n, line_no, "SHEET", "initial residue name", "18-20", "right", log_messages)
    compare_field(init_chain_o, init_chain_n, line_no, "SHEET", "initial chain identifier", "22", "left", log_messages)
    compare_field(init_seq_o, init_seq_n, line_no, "SHEET", "initial residue sequence number", "23-26", "right", log_messages)
    compare_field(init_icode_o, init_icode_n, line_no, "SHEET", "initial insertion code", "27", "left", log_messages)
    compare_field(end_res_o, end_res_n, line_no, "SHEET", "terminal residue name", "29-31", "right", log_messages)
    compare_field(end_chain_o, end_chain_n, line_no, "SHEET", "terminal chain identifier", "33", "left", log_messages)
    compare_field(end_seq_o, end_seq_n, line_no, "SHEET", "terminal residue sequence number", "34-37", "right", log_messages)
    compare_field(end_icode_o, end_icode_n, line_no, "SHEET", "terminal insertion code", "38", "left", log_messages)
    compare_field(sense_o, sense_n, line_no, "SHEET", "strand sense", "39-40", "right", log_messages)
    compare_field(cur_atom_o, cur_atom_n, line_no, "SHEET", "current atom name", "42-45", "left", log_messages)
    compare_field(cur_res_o, cur_res_n, line_no, "SHEET", "current residue name", "46-48", "right", log_messages)
    compare_field(cur_chain_o, cur_chain_n, line_no, "SHEET", "current chain identifier", "50", "left", log_messages)
    compare_field(cur_seq_o, cur_seq_n, line_no, "SHEET", "current residue sequence number", "51-54", "right", log_messages)
    compare_field(cur_icode_o, cur_icode_n, line_no, "SHEET", "current insertion code", "55", "left", log_messages)
    compare_field(prev_atom_o, prev_atom_n, line_no, "SHEET", "previous atom name", "57-60", "left", log_messages)
    compare_field(prev_res_o, prev_res_n, line_no, "SHEET", "previous residue name", "61-63", "right", log_messages)
    compare_field(prev_chain_o, prev_chain_n, line_no, "SHEET", "previous chain identifier", "65", "left", log_messages)
    compare_field(prev_seq_o, prev_seq_n, line_no, "SHEET", "previous residue sequence number", "66-69", "right", log_messages)
    compare_field(prev_icode_o, prev_icode_n, line_no, "SHEET", "previous insertion code", "70", "left", log_messages)

    newline = (
        rec_n
        + " "
        + strand_n
        + " "
        + sheet_id_n
        + nstrands_n
        + " "
        + init_res_n
        + " "
        + init_chain_n
        + init_seq_n
        + init_icode_n
        + " "
        + end_res_n
        + " "
        + end_chain_n
        + end_seq_n
        + end_icode_n
        + sense_n
        + " "
        + cur_atom_n
        + cur_res_n
        + " "
        + cur_chain_n
        + cur_seq_n
        + cur_icode_n
        + " "
        + prev_atom_n
        + prev_res_n
        + " "
        + prev_chain_n
        + prev_seq_n
        + prev_icode_n
    )
    return newline + "\n"


def format_ssbond(line: str, line_no: int, log_messages: List[str]) -> str:
    rec_o = safe_slice(line, 1, 6)
    serial_o = safe_slice(line, 8, 10)
    res1_o = safe_slice(line, 12, 14)
    chain1_o = safe_slice(line, 16, 16)
    seq1_o = safe_slice(line, 18, 21)
    icode1_o = safe_slice(line, 22, 22)
    res2_o = safe_slice(line, 26, 28)
    chain2_o = safe_slice(line, 30, 30)
    seq2_o = safe_slice(line, 32, 35)
    icode2_o = safe_slice(line, 36, 36)
    sym1_o = safe_slice(line, 60, 65)
    sym2_o = safe_slice(line, 67, 72)
    length_o = safe_slice(line, 74, 78)

    serial = parse_int(serial_o)
    res1 = res1_o.strip()
    chain1 = chain1_o.strip()
    seq1 = parse_int(seq1_o)
    icode1 = icode1_o.strip()
    res2 = res2_o.strip()
    chain2 = chain2_o.strip()
    seq2 = parse_int(seq2_o)
    icode2 = icode2_o.strip()
    sym1 = parse_int(sym1_o)
    sym2 = parse_int(sym2_o)
    length = parse_float(length_o)

    if serial is None:
        serial = 0
        add_change(log_messages, line_no, "SSBOND", "serial fixed -> 0")
    if seq1 is None:
        seq1 = 0
        add_change(log_messages, line_no, "SSBOND", "first residue sequence fixed -> 0")
    if seq2 is None:
        seq2 = 0
        add_change(log_messages, line_no, "SSBOND", "second residue sequence fixed -> 0")
    if sym1 is None:
        sym1 = 0
        add_change(log_messages, line_no, "SSBOND", "first symmetry operator fixed -> 0")
    if sym2 is None:
        sym2 = 0
        add_change(log_messages, line_no, "SSBOND", "second symmetry operator fixed -> 0")
    if length is None:
        length = 0.00
        add_change(log_messages, line_no, "SSBOND", "bond length fixed -> 0.00")

    rec_n = left("SSBOND", 6)
    serial_n = int_field(serial, 3)
    res1_n = right(res1, 3)
    chain1_n = left(chain1, 1)
    seq1_n = int_field(seq1, 4)
    icode1_n = left(icode1, 1)
    res2_n = right(res2, 3)
    chain2_n = left(chain2, 1)
    seq2_n = int_field(seq2, 4)
    icode2_n = left(icode2, 1)
    sym1_n = int_field(sym1, 6)
    sym2_n = int_field(sym2, 6)
    length_n = float_field(length, 5, 2)

    compare_field(rec_o, rec_n, line_no, "SSBOND", "record type", "1-6", "left", log_messages)
    compare_field(serial_o, serial_n, line_no, "SSBOND", "serial number", "8-10", "right", log_messages)
    compare_field(res1_o, res1_n, line_no, "SSBOND", "first residue name", "12-14", "right", log_messages)
    compare_field(chain1_o, chain1_n, line_no, "SSBOND", "first chain identifier", "16", "left", log_messages)
    compare_field(seq1_o, seq1_n, line_no, "SSBOND", "first residue sequence number", "18-21", "right", log_messages)
    compare_field(icode1_o, icode1_n, line_no, "SSBOND", "first insertion code", "22", "left", log_messages)
    compare_field(res2_o, res2_n, line_no, "SSBOND", "second residue name", "26-28", "right", log_messages)
    compare_field(chain2_o, chain2_n, line_no, "SSBOND", "second chain identifier", "30", "left", log_messages)
    compare_field(seq2_o, seq2_n, line_no, "SSBOND", "second residue sequence number", "32-35", "right", log_messages)
    compare_field(icode2_o, icode2_n, line_no, "SSBOND", "second insertion code", "36", "left", log_messages)
    compare_field(sym1_o, sym1_n, line_no, "SSBOND", "first symmetry operator", "60-65", "right", log_messages)
    compare_field(sym2_o, sym2_n, line_no, "SSBOND", "second symmetry operator", "67-72", "right", log_messages)
    compare_field(length_o, length_n, line_no, "SSBOND", "disulfide bond length", "74-78", "right", log_messages)

    newline = (
        rec_n
        + " "
        + serial_n
        + " "
        + res1_n
        + " "
        + chain1_n
        + " "
        + seq1_n
        + icode1_n
        + "   "
        + res2_n
        + " "
        + chain2_n
        + " "
        + seq2_n
        + icode2_n
        + (" " * 23)
        + sym1_n
        + " "
        + sym2_n
        + " "
        + length_n
    )
    return newline + "\n"


# ============================================================
# Main processing
# ============================================================

def process_pdb(input_path: Path, output_path: Path, log_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    log_messages: List[str] = []
    output_lines: List[str] = []

    with input_path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            record = safe_slice(line, 1, 6).strip().upper()

            try:
                if record == "ATOM":
                    output_lines.append(format_atom_like("ATOM", line, line_no, log_messages))
                elif record == "HETATM":
                    output_lines.append(format_atom_like("HETATM", line, line_no, log_messages))
                elif record == "TER":
                    output_lines.append(format_ter(line, line_no, log_messages))
                elif record == "HELIX":
                    output_lines.append(format_helix(line, line_no, log_messages))
                elif record == "SHEET":
                    output_lines.append(format_sheet(line, line_no, log_messages))
                elif record == "SSBOND":
                    output_lines.append(format_ssbond(line, line_no, log_messages))
                else:
                    output_lines.append(raw_line if raw_line.endswith("\n") else raw_line + "\n")

            except Exception as exc:
                output_lines.append(raw_line if raw_line.endswith("\n") else raw_line + "\n")
                add_change(
                    log_messages,
                    line_no,
                    record if record else "UNKNOWN",
                    f"could not reformat -> preserved original ({exc})"
                )

    with output_path.open("w", encoding="utf-8") as f:
        f.writelines(output_lines)

    with log_path.open("w", encoding="utf-8") as f:
        for msg in log_messages:
            f.write(msg + "\n")


def build_default_names(input_path: Path) -> Tuple[Path, Path]:
    stem = input_path.stem
    parent = input_path.parent
    return (
        parent / f"{stem}_standardized.pdb",
        parent / f"{stem}_standardized.log",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strictly standardize a PDB file and log every field-level change."
    )
    parser.add_argument("input_pdb", help="Input PDB file")
    parser.add_argument("-o", "--output", help="Output standardized PDB file")
    parser.add_argument("-l", "--log", help="Log file containing changes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_path = Path(args.input_pdb)
    default_output, default_log = build_default_names(input_path)

    output_path = Path(args.output) if args.output else default_output
    log_path = Path(args.log) if args.log else default_log

    try:
        process_pdb(input_path, output_path, log_path)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print(f"Standardized PDB written to: {output_path}")
    print(f"Change log written to: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
