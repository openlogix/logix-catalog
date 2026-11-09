"""Tests for tools/check.py: the formatter, and each rule with a board that
breaks it."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check  # noqa: E402

FPGAS, FPGA_PROBLEMS = check.load_fpgas()
GOOD = {
    "$schema": check.BOARD_SCHEMA,
    "name": "Test board",
    "fpga_id": "ice40up5k-sg48",
    "variants": [
        {
            "selector": {"connection": "usb", "memory": "flash"},
            "programmer": "iceprog",
            "args": "-d d:${BUS}/${DEV} ${BITSTREAM}",
            "usb": {"vid": "0403", "pid": "6014"},
            "tested": True,
        }
    ],
    "resources": {
        "clk": {"type": "clock", "pin": "35", "mhz": 12},
        "led": {"type": "leds", "pins": ["37"], "active": "low"},
    },
}
BOARD = check.schema()


def problems(board):
    """Schema errors as (path, message), else the checker's own problems."""
    errors = [("/".join(map(str, e.absolute_path)), e.message) for e in BOARD.iter_errors(board)]
    return errors or check.board_problems(board, FPGAS)


class Catalog(unittest.TestCase):
    def test_the_catalog_is_fine(self):
        self.assertEqual(check.check(), [])

    def test_a_good_board(self):
        self.assertEqual(problems(GOOD), [])

    def test_schema_errors(self):
        for change in [
            lambda b: b.pop("name"),
            lambda b: b.update(extra=1),
            lambda b: b["resources"].update({"2clk": {"type": "clock", "pin": "1", "mhz": 1}}),
            lambda b: b["resources"]["clk"].update(mhz=0),
            lambda b: b["resources"]["clk"].pop("pin"),
            lambda b: b["resources"]["led"].update(type="lamp"),
            lambda b: b["resources"]["led"].update(active="on"),
            lambda b: b["resources"].update(p={"type": "pmod", "pins": ["1", "2"]}),
            lambda b: b["variants"][0].update(programmer="apio"),
            lambda b: b["variants"][0]["usb"].update(vid="403"),
        ]:
            b = copy.deepcopy(GOOD)
            change(b)
            self.assertTrue(problems(b), b)

    def test_rules_beyond_the_schema(self):
        b = copy.deepcopy(GOOD)
        b["fpga_id"] = "no-such-fpga"
        self.assertIn(("fpga_id", "'no-such-fpga' isn't in fpgas/."), problems(b))
        b = copy.deepcopy(GOOD)
        b["resources"]["led"]["pins"] = ["37", "37"]
        self.assertEqual(problems(b), [("resources/led", "Pin 37 is in this resource twice.")])
        b = copy.deepcopy(GOOD)
        b["resources"]["clk"]["io_standard"] = "LVCMOS33"
        self.assertEqual(
            problems(b), [("resources/clk/io_standard", "LVCMOS33 isn't an I/O standard for ice40 (allowed: none).")]
        )
        b = copy.deepcopy(GOOD)
        b["variants"].append(copy.deepcopy(b["variants"][0]))
        self.assertEqual(problems(b), [("variants/1/selector", "Another variant has the selector usb, flash.")])
        b = copy.deepcopy(GOOD)
        b["variants"][0]["args"] = "${PORT}"
        self.assertEqual(problems(b), [("variants/0/args", "Unknown variable ${PORT}.")])
        b = copy.deepcopy(GOOD)
        ram = copy.deepcopy(b["variants"][0])
        ram["selector"]["memory"] = "ram"
        b["variants"].insert(0, ram)
        self.assertEqual(problems(b)[0][0], "variants/0")

    def test_requirements(self):
        drive = {"type": "drive", "name": "en", "pins": ["2"], "level": "high", "why": "Turns the LEDs on."}
        setup = {"type": "setup", "text": "Close jumper J1."}
        b = copy.deepcopy(GOOD)
        b["requires"] = [drive]
        b["resources"]["clk"]["requires"] = [setup]
        b["resources"]["led"]["requires"] = [dict(drive, name="led_en", pins=["3"], level="low")]
        self.assertEqual(problems(b), [])
        # Schema: a known type, its required fields, a level, no empty list.
        for change in [
            lambda b: b["requires"][0].update(type="wire"),
            lambda b: b["requires"][0].pop("level"),
            lambda b: b["requires"][0].update(level="up"),
            lambda b: b["requires"][0].update(name="2en"),
            lambda b: b["requires"][0].update(pins=[]),
            lambda b: b["resources"]["clk"]["requires"][0].update(text=""),
            lambda b: b["resources"]["clk"].update(requires=[]),
        ]:
            c = copy.deepcopy(b)
            change(c)
            self.assertTrue(problems(c), c)
        # Beyond the schema: names unique on the board, pins once, I/O standard.
        c = copy.deepcopy(b)
        c["requires"][0].update(name="led", pins=["2", "2"], io_standard="LVCMOS33")
        self.assertEqual(problems(c), [
            ("requires/0/name", "Another resource or drive is named led."),
            ("requires/0/pins", "Pin 2 is in this drive twice."),
            ("requires/0/io_standard", "LVCMOS33 isn't an I/O standard for ice40 (allowed: none)."),
        ])
        c = copy.deepcopy(b)
        c["resources"]["led"]["requires"][0]["name"] = "en"
        self.assertEqual(problems(c), [("resources/led/requires/0/name", "Another resource or drive is named en.")])

    def test_resources_may_share_pins(self):
        b = copy.deepcopy(GOOD)
        b["resources"]["pmod"] = {"type": "pmod", "pins": ["37", "2", "3", "4", "5", "6", "7", "8"]}
        self.assertEqual(problems(b), [])

    def test_fpga_files(self):
        self.assertEqual(FPGA_PROBLEMS, [])
        self.assertEqual(FPGAS["ice40up5k-sg48"]["family"], "ice40")
        self.assertEqual({f["family"] for f in FPGAS.values()}, set(check.FAMILIES))
        part = {"part_number": "P", "size": "1k", "nextpnr_device": "d", "nextpnr_package": "p"}
        ice40 = {"$schema": check.fpgas_schema_url("ice40")}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "fpgas"
            folder.mkdir()
            ecp5 = {**part, "part_number": "LFE5U-12F", "nextpnr_speed": "6"}
            (folder / "ecp5.json").write_text(json.dumps({"$schema": check.fpgas_schema_url("ecp5"), "a": ecp5}))
            (folder / "ice40.json").write_text(json.dumps({**ice40, "a": part, "b": {**part, "part_number": "ICE40HX1K"}}))
            (folder / "gw1n.json").write_text(json.dumps({"$schema": check.fpgas_schema_url("ice40"), "g": part}))
            gw2a = {"part_number": "GW1N-1", "size": "1k", "nextpnr_device": "d", "packer_device": "p"}
            (folder / "gw2a.json").write_text(json.dumps({"$schema": check.fpgas_schema_url("gowin"), "h": gw2a}))
            (folder / "artix7.json").write_text(json.dumps({"$schema": check.fpgas_schema_url("openxc7"), "B": part}))
            (folder / "gowin.json").write_text("{}")
            fpgas, found = check.load_fpgas(Path(tmp))
        self.assertEqual(sorted(fpgas), ["a", "b", "h"])
        self.assertEqual(fpgas["a"]["family"], "ecp5")
        self.assertEqual(fpgas["h"]["family"], "gw2a")
        self.assertEqual(found, [
            ("fpgas/artix7.json", "(file)", "'B' does not match '^(\\\\$schema|[a-z0-9]+(-[a-z0-9]+)*)$'"),
            ("fpgas/artix7.json", "B", "Additional properties are not allowed ('nextpnr_package' was unexpected)"),
            ("fpgas/gowin.json", "name", "'gowin' isn't one of ['artix7', 'ecp5', 'gw1n', 'gw2a', 'gw5a', 'ice40', 'spartan7', 'zynq7000']."),
            ("fpgas/gw1n.json", "$schema", "'https://www.openlogix.org/schemas/logix-fpgas-gowin-v1.json' was expected"),
            ("fpgas/gw1n.json", "g", "'packer_device' is a required property"),
            ("fpgas/gw1n.json", "g", "Additional properties are not allowed ('nextpnr_package' was unexpected)"),
            ("fpgas/gw2a.json", "h/part_number", "GW1N-1 isn't a gw2a part: its part number starts with GW2A."),
            ("fpgas/ice40.json", "a", "Also in fpgas/ecp5.json: an FPGA ID is in one file only."),
        ])
        # The schemas check fields and IDs.
        errors = check.schema_errors(check.fpgas_schema("ice40"), {**ice40, "B": {**part, "family": "ice40"}})
        self.assertEqual([w for w, _ in errors], ["(file)", "B"])
        self.assertIn("'B' does not match", errors[0][1])
        self.assertIn("'family' was unexpected", errors[1][1])

    def test_canonical_format(self):
        text = check.canonical_file({"a": {"b": [1, 2]}, "c": ["x" * 120]})
        self.assertEqual(text, '{\n  "a": {"b": [1, 2]},\n  "c": [\n    "' + "x" * 120 + '"\n  ]\n}\n')
        self.assertEqual(check.canonical_file({}), "{}\n")


if __name__ == "__main__":
    unittest.main()
