"""Tests for tools/check.py: the formatter, and each rule with a board that
breaks it."""

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check  # noqa: E402

FPGAS = json.loads((ROOT / "fpgas.json").read_text())
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
        self.assertIn(("fpga_id", "'no-such-fpga' isn't in fpgas.json."), problems(b))
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

    def test_resources_may_share_pins(self):
        b = copy.deepcopy(GOOD)
        b["resources"]["pmod"] = {"type": "pmod", "pins": ["37", "2", "3", "4", "5", "6", "7", "8"]}
        self.assertEqual(problems(b), [])

    def test_canonical_format(self):
        text = check.canonical_file({"a": {"b": [1, 2]}, "c": ["x" * 120]})
        self.assertEqual(text, '{\n  "a": {"b": [1, 2]},\n  "c": [\n    "' + "x" * 120 + '"\n  ]\n}\n')
        self.assertEqual(check.canonical_file({}), "{}\n")


if __name__ == "__main__":
    unittest.main()
