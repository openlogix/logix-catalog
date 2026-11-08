# Logix Catalog

Every FPGA board, described once.

Logix Catalog is the open catalog of FPGA boards behind every Logix tool: each board's FPGA, how to program it, and what its pins are wired to, from clocks and LEDs to PMOD headers. It's one readable JSON file per board. [Logix Engine](https://www.openlogix.org/engine/) builds it in, and other projects can use the data too. See the [Logix Catalog page](https://www.openlogix.org/catalog/).

**In development.** The format may still change before the first release.

## What's here

- [`boards/`](boards/): one file per board, `boards/<id>.json`.
- [`fpgas/`](fpgas): every FPGA the toolchain supports, by ID, one file per FPGA family (`ice40.json`, `ecp5.json`, `gowin.json`, `xilinx.json`).
- [`schemas/`](schemas/): the JSON Schemas, also served at `www.openlogix.org/schemas/`.
- [`docs/model.md`](docs/model.md): how a board is described.
- [`docs/design.md`](docs/design.md): why it's shaped this way, and how Logix Engine uses it.
- [`tools/check.py`](tools/check.py): checks the catalog.

## Adding or fixing a board

1. Copy a similar board's file to `boards/<new-id>.json`, or edit the board's file.
2. Fill in what you know; leave out what you don't. Say where a fact comes from with `source` (see [the model](docs/model.md)).
3. Run `scripts/test.sh` (Python 3). It checks every board and formats files the canonical way with `tools/check.py --fix`.
4. Open a pull request.

## License

Licensed under [MIT](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), at your option. Logix Catalog is part of [Open Logix](https://www.openlogix.org/): free, open source tools for FPGA design.
