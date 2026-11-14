"""The docs site's board and FPGA lists, written from the catalog's files.

Two Markdown pages for people: "Predefined boards" (boards.md) and
"Supported FPGAs" (fpgas.md). tools/mkdocs_hooks.py adds them to the docs
site at build time, so they always match the catalog on main and are never
committed. Reading the files directly is this repo's own maintenance (the
shared rule: everyone else reads the catalog through Logix Engine).
"""

import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The families in the order people see them, with their names and makers.
# The keys are the FPGA files' names (fpgas/<family>.json).
FAMILY_NAMES = {
    "ice40": ("iCE40", "Lattice"),
    "ecp5": ("ECP5", "Lattice"),
    "gw1n": ("GW1N (LittleBee)", "Gowin"),
    "gw2a": ("GW2A (Arora)", "Gowin"),
    "gw5a": ("GW5A (Arora V)", "Gowin"),
    "artix7": ("Artix-7", "AMD (Xilinx)"),
    "spartan7": ("Spartan-7", "AMD (Xilinx)"),
    "zynq7000": ("Zynq-7000", "AMD (Xilinx)"),
}

# How a variant's connection reads (docs/model.md, Variants).
CONNECTIONS = {
    "usb": "USB",
    "bootloader": "USB bootloader",
    "ft2232h": "FT2232H adapter",
    "ft232h": "FT232H adapter",
    "cmsis-dap": "CMSIS-DAP adapter",
    "usb-blaster": "USB-Blaster",
    "unspecified": "Programmer",
}
MEMORIES = {"flash": "flash", "ram": "RAM"}

IDE_OWN_BOARDS = "https://www.openlogix.org/logix-ide/using-logix/#your-own-boards"
CONTRIBUTE = "https://github.com/openlogix/logix-catalog/pulls"


def load(root=ROOT):
    """Returns (fpgas, boards): fpgas[family] = {id: fpga}, boards = {id: board}."""
    fpgas = {}
    for family in FAMILY_NAMES:
        data = json.loads((root / "fpgas" / f"{family}.json").read_text())
        fpgas[family] = {k: v for k, v in data.items() if k != "$schema"}
    boards = {p.stem: json.loads(p.read_text()) for p in sorted((root / "boards").glob("*.json"))}
    return fpgas, boards


def size_key(size):
    """Sorts sizes such as 384, 1k, 25k by number."""
    match = re.fullmatch(r"(\d+)(k?)", size)
    return int(match.group(1)) * (1000 if match.group(2) else 1) if match else 0


def part(fpga):
    """The FPGA's part number, kept on one line in tables."""
    return f'<span style="white-space: nowrap">{fpga["part_number"]}</span>'


def plural(count, word):
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def programming(board):
    """How a board can be programmed, such as "USB: flash, RAM"."""
    by_connection = collections.defaultdict(list)
    for variant in board["variants"]:
        selector = variant["selector"]
        by_connection[selector["connection"]].append(MEMORIES[selector["memory"]])
    return "<br>".join(f"{CONNECTIONS[c]}: {', '.join(m)}" for c, m in by_connection.items())


def on_board(board):
    """What the board has, such as "12 MHz clock · 3 LEDs · RGB LED"."""
    resources = list(board.get("resources", {}).values())
    by_type = collections.defaultdict(list)
    for resource in resources:
        by_type[resource["type"]].append(resource)
    parts = []
    clocks = [f"{r['mhz']:g} MHz" for r in by_type["clock"]]
    if clocks:
        parts.append(", ".join(clocks) + (" clock" if len(clocks) == 1 else " clocks"))
    leds = sum(len(r["pins"]) for r in by_type["leds"])
    if leds:
        parts.append(plural(leds, "LED"))
    rgb = len(by_type["rgb_led"]) + sum(len(r["leds"]) for r in by_type["led_matrix"])
    if rgb:
        parts.append("RGB LED" if rgb == 1 else f"{rgb} RGB LEDs")
    switches = sum(len(r["pins"]) for r in by_type["switches"])
    if switches:
        parts.append(plural(switches, "switch").replace("switchs", "switches"))
    if by_type["pmod"]:
        parts.append(f"{len(by_type['pmod'])} PMOD")
    if by_type["header"]:
        parts.append(plural(len(by_type["header"]), "header"))
    if by_type["uart"]:
        parts.append("UART")
    return " · ".join(parts)


def boards_page(root=ROOT):
    fpgas, boards = load(root)
    family_of = {fpga_id: family for family, ids in fpgas.items() for fpga_id in ids}
    by_family = collections.defaultdict(list)
    for board_id, board in boards.items():
        by_family[family_of[board["fpga_id"]]].append((board_id, board))
    lines = [
        "# Predefined boards",
        "",
        f"These are the boards Logix Catalog describes today: {len(boards)} boards, with FPGAs "
        f"from {len(by_family)} families. Open Logix tools such as Logix IDE list them for you, "
        "and Logix Engine builds designs for them and programs them.",
        "",
        "> [!TIP]",
        "> **Your board isn't here? Add your own.** Describe it in one file, in the catalog's "
        f"[board format](model.md), and your tool uses it like a predefined board, with any of the "
        f"[supported FPGAs](fpgas.md). In Logix IDE, see [Your own boards]({IDE_OWN_BOARDS}). "
        f"To add it to the catalog for everyone, send the file as a [pull request]({CONTRIBUTE}).",
        "",
        "This list follows the catalog's newest version: a board added recently reaches Open Logix "
        "tools with their next catalog update.",
    ]
    for family, (name, maker) in FAMILY_NAMES.items():
        if not by_family[family]:
            continue
        lines += [
            "",
            f"## {name}",
            "",
            f"{maker} · {plural(len(by_family[family]), 'board')}",
            "",
            "| Board | FPGA | Programming | On the board |",
            "| --- | --- | --- | --- |",
        ]
        for board_id, board in sorted(by_family[family], key=lambda b: b[1]["name"].lower()):
            fpga = fpgas[family][board["fpga_id"]]
            lines.append(
                f"| {board['name']}<br>`{board_id}` | {part(fpga)} | "
                f"{programming(board)} | {on_board(board)} |"
            )
    return "\n".join(lines) + "\n"


def fpgas_page(root=ROOT):
    fpgas, boards = load(root)
    boards_of = collections.defaultdict(list)
    for board in boards.values():
        boards_of[board["fpga_id"]].append(board["name"])
    total = sum(len(ids) for ids in fpgas.values())
    lines = [
        "# Supported FPGAs",
        "",
        f"Logix Engine builds designs for every FPGA here: {total} FPGAs in {len(fpgas)} families, "
        "every one the open source FPGA tools it downloads (Yosys, nextpnr and openXC7) support. "
        "A board with any of them works the same way, whether it's one of the "
        "[predefined boards](boards.md) or your own.",
        "",
        "*Size* is the FPGA's logic capacity as its maker names it, such as 5k for about 5,000 "
        "logic cells. *Boards* are the predefined boards with that FPGA.",
    ]
    for family, (name, maker) in FAMILY_NAMES.items():
        ids = fpgas[family]
        lines += [
            "",
            f"## {name}",
            "",
            f"{maker} · {plural(len(ids), 'FPGA')}",
            "",
            "| FPGA | Size | Boards |",
            "| --- | --- | --- |",
        ]
        for fpga_id, fpga in sorted(ids.items(), key=lambda i: (size_key(i[1]["size"]), i[1]["part_number"])):
            names = ", ".join(sorted(boards_of[fpga_id], key=str.lower))
            lines.append(f"| {part(fpga)} | {fpga['size']} | {names} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys

    print(fpgas_page() if sys.argv[1:] == ["fpgas"] else boards_page(), end="")
