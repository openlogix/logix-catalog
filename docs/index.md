# Logix Catalog Docs

These are Logix Catalog's docs. Its **main page**, what it is and how it's
used, is [www.openlogix.org/catalog](https://www.openlogix.org/catalog/);
the data and code are on [GitHub](https://github.com/openlogix/logix-catalog).

Every FPGA board, described once.

Logix Catalog is the open catalog of FPGA boards behind every Open Logix tool:
each board's FPGA, how to program it, and what its pins are wired to, from
clocks and LEDs to PMOD headers. It's one readable JSON file per board.
[Logix Engine](https://www.openlogix.org/engine/) builds it in and serves
it to every tool, yours included.

**In development.** The format may still change before the first release.

## Documentation

| Page | What it covers |
| --- | --- |
| [Board model](model.md) | How a board is described: its file, variants, resources, requirements and AI hints |
| [Design](design.md) | Why the catalog is shaped this way, how it grows, and how Logix Engine uses it |

## What's in the catalog

- [`boards/`](https://github.com/openlogix/logix-catalog/tree/main/boards): one file per board, `boards/<id>.json`.
- [`fpgas/`](https://github.com/openlogix/logix-catalog/tree/main/fpgas): every FPGA the toolchain supports, by ID, one file per FPGA family.
- [`schemas/`](https://github.com/openlogix/logix-catalog/tree/main/schemas): the JSON Schemas, also served at `www.openlogix.org/schemas/`.

## Using the data

The data is free to use, copy and change, under MIT or Apache 2.0. Tools,
scripts and agents are intended to get it through
[Logix Engine](https://www.openlogix.org/logix-engine/)'s API, the
supported interface, which every Open Logix tool uses. The files' layout may
change between releases; the board file format is stable for writing
boards. This isn't enforced; reading the files directly is at your own
risk.

## Adding or fixing a board

1. Copy a similar board's file to `boards/<new-id>.json`, or edit the
   board's file.
2. Fill in what you know; leave out what you don't. Say where a fact comes
   from with `source` (see the [board model](model.md)).
3. Run `scripts/test.sh` (Python 3). It checks every board and formats
   files the canonical way with `tools/check.py --fix`.
4. Open a [pull request](https://github.com/openlogix/logix-catalog/pulls).
