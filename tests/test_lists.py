"""Tests for tools/lists.py: the docs site's board and FPGA lists."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import lists  # noqa: E402


class ListsTest(unittest.TestCase):
    def test_every_board_is_listed_once(self):
        _, boards = lists.load()
        page = lists.boards_page()
        for board_id in boards:
            self.assertEqual(page.count(f"`{board_id}`"), 1, board_id)

    def test_every_fpga_is_listed(self):
        fpgas, _ = lists.load()
        page = lists.fpgas_page()
        rows = [line for line in page.splitlines() if line.startswith("| ") and not line.startswith(("| FPGA", "| ---"))]
        self.assertEqual(len(rows), sum(len(ids) for ids in fpgas.values()))
        for ids in fpgas.values():
            for fpga in ids.values():
                self.assertIn(f"| {lists.part(fpga)} |", page)

    def test_every_family_has_a_name(self):
        self.assertEqual(
            sorted(lists.FAMILY_NAMES),
            sorted(p.stem for p in (lists.ROOT / "fpgas").glob("*.json")),
        )

    def test_the_canonical_board_reads_well(self):
        _, boards = lists.load()
        board = boards["icesugar-1-5"]
        self.assertEqual(lists.programming(board), "USB: flash")
        self.assertIn("12 MHz clock", lists.on_board(board))
        self.assertIn("RGB LED", lists.on_board(board))

    def test_sizes_sort_by_number(self):
        self.assertEqual(sorted(["25k", "384", "1k", "5k"], key=lists.size_key), ["384", "1k", "5k", "25k"])


if __name__ == "__main__":
    unittest.main()
