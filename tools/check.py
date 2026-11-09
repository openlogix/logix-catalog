#!/usr/bin/env python3
"""Checks Logix Catalog: every board file and FPGA file against its schema,
the rules the schemas can't express, and the canonical formatting.

    tools/check.py          check everything, exit 1 on any problem
    tools/check.py --fix    also rewrite files in the canonical format

Problems print as "<file>: <where>: <what>", one per line.
"""

import json
import re
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
BOARD_SCHEMA = "https://www.openlogix.org/schemas/logix-board-v1.json"


def fpgas_schema_url(schema):
    """The address of an FPGA schema, which the FPGA files that use it name."""
    return f"https://www.openlogix.org/schemas/logix-fpgas-{schema}-v1.json"

# The FPGA families, one file each, fpgas/<family>.json: each family's
# schema, shared by the families whose FPGAs have the same fields, and the
# start of its part numbers.
FAMILIES = {
    "ice40": ("ice40", ("ICE40", "ICE5")),
    "ecp5": ("ecp5", ("LFE5",)),
    "gw1n": ("gowin", ("GW1N",)),
    "gw2a": ("gowin", ("GW2A",)),
    "gw5a": ("gowin", ("GW5A",)),
    "artix7": ("openxc7", ("XC7A",)),
    "spartan7": ("openxc7", ("XC7S",)),
    "zynq7000": ("openxc7", ("XC7Z",)),
}
# The I/O standards each schema's families' pin files can name. iCE40 pin
# files have no per-pin standard.
SEVEN = {"LVCMOS33", "LVCMOS25", "LVCMOS18", "LVCMOS15", "LVCMOS12", "LVTTL", "LVDS", "SSTL15", "SSTL135"}
IO_STANDARDS = {
    "ice40": set(),
    "ecp5": SEVEN - {"LVTTL"},
    "gowin": SEVEN,
    "openxc7": SEVEN,
}


def io_standards(family):
    """The I/O standards a family's pin files can name."""
    return IO_STANDARDS[FAMILIES[family][0]]
TEMPLATE_VARIABLES = {"VID", "PID", "BUS", "DEV", "SERIAL_NUM", "USB_PATH", "BITSTREAM"}
WIDTH = 100


def flat(value):
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def canonical(value, indent=0, prefix=""):
    """The canonical text of a JSON value whose line starts at column
    `indent` with `prefix` (such as a key) before it: two-space indents, and
    any object or array that fits on its line within WIDTH columns written on
    one line. The whole file's top level is always expanded."""
    one = flat(value)
    if not isinstance(value, (dict, list)) or not value:
        return prefix + one
    if indent > 0 and indent + len(prefix) + len(one) <= WIDTH:
        return prefix + one
    pad = " " * (indent + 2)
    if isinstance(value, dict):
        items = [pad + canonical(v, indent + 2, json.dumps(k, ensure_ascii=False) + ": ").lstrip(" ") for k, v in value.items()]
        open_, close = "{", "}"
    else:
        items = [pad + canonical(v, indent + 2) for v in value]
        open_, close = "[", "]"
    return prefix + open_ + "\n" + ",\n".join(items) + "\n" + " " * indent + close


def hints_last(value):
    """The value with every object's `ai_hints` moved to its end."""
    if isinstance(value, list):
        return [hints_last(v) for v in value]
    if not isinstance(value, dict):
        return value
    out = {k: hints_last(v) for k, v in value.items() if k != "ai_hints"}
    if "ai_hints" in value:
        out["ai_hints"] = value["ai_hints"]
    return out


def canonical_file(value):
    """A file's canonical text: `canonical`, with `ai_hints` last in every
    object."""
    return canonical(hints_last(value)) + "\n"


def schema():
    """The board schema's validator."""
    board = json.loads((ROOT / "schemas/logix-board-v1.json").read_text())
    return jsonschema.Draft202012Validator(board)


def fpgas_schema(schema):
    """The validator of an FPGA schema's files."""
    s = json.loads((ROOT / f"schemas/logix-fpgas-{schema}-v1.json").read_text())
    return jsonschema.Draft202012Validator(s)


def schema_errors(validator, data):
    """A validator's errors, as (where, what), in file order."""
    errors = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    return [("/".join(str(p) for p in e.absolute_path) or "(file)", e.message) for e in errors]


def resource_pins(r):
    """A resource's pins, as (field, pin) pairs, nulls left out."""
    out = []
    for field in ("pin", "red", "green", "blue", "tx", "rx", "rts", "cts"):
        if field in r:
            out.append((field, r[field]))
    for field in ("pins", "leds"):
        for i, p in enumerate(r.get(field, [])):
            if p is not None:
                out.append((f"{field}/{i}", p))
    for color, p in r.get("colors", {}).items():
        out.append((f"colors/{color}", p))
    return out


def board_problems(board, fpgas):
    """The problems the schema can't express, as (where, what) pairs."""
    out = []
    fpga = fpgas.get(board.get("fpga_id"))
    if fpga is None:
        out.append(("fpga_id", f"{board.get('fpga_id')!r} isn't in fpgas/."))
    family = fpga["family"] if fpga else None
    variants = board.get("variants", [])
    seen = set()
    for i, v in enumerate(variants):
        sel = (v["selector"]["connection"], v["selector"]["memory"])
        if sel in seen:
            out.append((f"variants/{i}/selector", f"Another variant has the selector {sel[0]}, {sel[1]}."))
        seen.add(sel)
        for var in re.findall(r"\$\{([^}]*)\}", v["args"]):
            if var not in TEMPLATE_VARIABLES:
                out.append((f"variants/{i}/args", f"Unknown variable ${{{var}}}."))
    if any(v["selector"]["memory"] == "flash" for v in variants) and variants[0]["selector"]["memory"] != "flash":
        out.append(("variants/0", "The default variant, the first, must write flash when the board has a flash variant."))
    out += requirement_problems(board, family)
    for name, r in board.get("resources", {}).items():
        pins = resource_pins(r)
        dup = {p for _, p in pins if [q for _, q in pins].count(p) > 1}
        for p in sorted(dup):
            out.append((f"resources/{name}", f"Pin {p} is in this resource twice."))
        std = r.get("io_standard")
        if std is not None and family is not None and std not in io_standards(family):
            allowed = ", ".join(sorted(io_standards(family))) or "none"
            out.append((f"resources/{name}/io_standard", f"{std} isn't an I/O standard for {family} (allowed: {allowed})."))
    return out


def requirement_problems(board, family):
    """Problems in the board's and its resources' `requires`: a drive's
    name is a port name no resource or other drive has, its pins are in it
    once, and its I/O standard fits the FPGA family."""
    out = []
    names = set(board.get("resources", {}))
    places = [("requires", board.get("requires", []))]
    places += [(f"resources/{n}/requires", r.get("requires", [])) for n, r in board.get("resources", {}).items()]
    for where, reqs in places:
        for i, q in enumerate(reqs):
            if q["type"] != "drive":
                continue
            at = f"{where}/{i}"
            if q["name"] in names:
                out.append((f"{at}/name", f"Another resource or drive is named {q['name']}."))
            names.add(q["name"])
            dup = {p for p in q["pins"] if q["pins"].count(p) > 1}
            for p in sorted(dup):
                out.append((f"{at}/pins", f"Pin {p} is in this drive twice."))
            std = q.get("io_standard")
            if std is not None and family is not None and std not in io_standards(family):
                allowed = ", ".join(sorted(io_standards(family))) or "none"
                out.append((f"{at}/io_standard", f"{std} isn't an I/O standard for {family} (allowed: {allowed})."))
    return out


def load_fpgas(root=ROOT):
    """The FPGAs of every fpgas/<family>.json, by ID, each with its `family`
    taken from its file's name, and the problems found, as (file, where,
    what)."""
    fpgas, problems = {}, []
    for path in sorted((root / "fpgas").glob("*.json")):
        rel = str(path.relative_to(root))
        family = path.stem
        if family not in FAMILIES:
            problems.append((rel, "name", f"{family!r} isn't one of {sorted(FAMILIES)}."))
            continue
        schema_name, prefixes = FAMILIES[family]
        try:
            entries = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append((rel, f"line {e.lineno}", e.msg))
            continue
        found = schema_errors(fpgas_schema(schema_name), entries)
        problems += [(rel, w, t) for w, t in found]
        if found:
            continue
        for fid, f in entries.items():
            if fid == "$schema":
                continue
            if fid in fpgas:
                problems.append((rel, fid, f"Also in fpgas/{fpgas[fid]['family']}.json: an FPGA ID is in one file only."))
                continue
            if not f["part_number"].startswith(prefixes):
                problems.append((rel, f"{fid}/part_number", f"{f['part_number']} isn't a {family} part: its part number starts with {' or '.join(prefixes)}."))
            fpgas[fid] = {"family": family, **f}
    return fpgas, problems


def check(fix=False):
    """All problems, as "<file>: <where>: <what>" lines."""
    problems = []
    board_validator = schema()
    fpgas, fpga_found = load_fpgas()
    problems += [f"{p}: {w}: {t}" for p, w, t in fpga_found]
    fpga_files = sorted((ROOT / "fpgas").glob("*.json"))
    board_files = sorted((ROOT / "boards").glob("*.json"))
    for path in board_files:
        rel = path.relative_to(ROOT)
        bid = path.stem
        if not re.fullmatch(r"[a-z0-9-]+", bid):
            problems.append(f"{rel}: name: A board ID uses lowercase letters, digits and dashes.")
        try:
            board = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{rel}: line {e.lineno}: {e.msg}")
            continue
        errors = sorted(board_validator.iter_errors(board), key=lambda e: list(e.absolute_path))
        for e in errors:
            where = "/".join(str(p) for p in e.absolute_path) or "(file)"
            problems.append(f"{rel}: {where}: {e.message}")
        if not errors:
            problems += [f"{rel}: {w}: {t}" for w, t in board_problems(board, fpgas)]
    for path in fpga_files + board_files:
        text = path.read_text()
        try:
            want = canonical_file(json.loads(text))
        except json.JSONDecodeError:
            continue
        if text != want:
            if fix:
                path.write_text(want)
            else:
                problems.append(f"{path.relative_to(ROOT)}: (file): Not in the canonical format: run tools/check.py --fix.")
    return problems


def main():
    problems = check(fix="--fix" in sys.argv[1:])
    for p in problems:
        print(p)
    boards = len(list((ROOT / "boards").glob("*.json")))
    if problems:
        print(f"{len(problems)} problems.")
        sys.exit(1)
    print(f"All {boards} boards are fine.")


if __name__ == "__main__":
    main()
