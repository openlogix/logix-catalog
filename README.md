<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.openlogix.org/brand/readme/catalog-dark.svg">
  <img alt="Logix Catalog" src="https://www.openlogix.org/brand/readme/catalog-light.svg" height="96">
</picture>

[![License: MIT or Apache 2.0](https://img.shields.io/badge/License-MIT%20or%20Apache%202.0-blue)](#license)

[![test](https://img.shields.io/github/actions/workflow/status/openlogix/logix-catalog/test.yaml?branch=main&event=schedule&label=test)](https://github.com/openlogix/logix-catalog/actions/workflows/test.yaml)
[![build](https://img.shields.io/github/actions/workflow/status/openlogix/logix-catalog/build-pre-release.yaml?branch=main&event=schedule&label=build)](https://github.com/openlogix/logix-catalog/actions/workflows/build-pre-release.yaml)
[![docs](https://img.shields.io/github/actions/workflow/status/openlogix/logix-catalog/publish-docs.yaml?branch=main&event=schedule&label=docs)](https://github.com/openlogix/logix-catalog/actions/workflows/publish-docs.yaml)

**[Main page](https://www.openlogix.org/catalog/)** · [Docs](https://www.openlogix.org/logix-catalog/) · GitHub (here)

Every FPGA board, described once.

Logix Catalog is the open catalog of FPGA boards behind every Open Logix tool: each board's FPGA, how to program it, and what its pins are wired to, from clocks and LEDs to PMOD headers. It's one readable JSON file per board. [Logix Engine](https://www.openlogix.org/engine/) downloads it and serves it to every tool, yours included; the data is free to use and copy.

**In development.** The format may still change before the first release.

## What's here

- [`boards/`](boards/): one file per board, `boards/<id>.json`.
- [`fpgas/`](fpgas): every FPGA the toolchain supports, by ID, one file per FPGA family (`ice40.json`, `ecp5.json`, `gw1n.json`, `gw2a.json`, `gw5a.json`, `artix7.json`, `spartan7.json`, `zynq7000.json`).
- [`schemas/`](schemas/): the JSON Schemas, also served at `www.openlogix.org/schemas/`.
- [`docs/model.md`](docs/model.md): how a board is described.
- [`docs/design.md`](docs/design.md): why it's shaped this way, and how Logix Engine uses it.
- [`tools/check.py`](tools/check.py): checks the catalog.

## Using the data

The data is free to use, copy and change, under MIT or Apache 2.0. Tools, scripts and agents are intended to get it through [Logix Engine](https://www.openlogix.org/engine/)'s API, the supported interface, which every Open Logix tool uses. The files' layout may change between releases; the board file format is stable for writing boards. This isn't enforced; reading the files directly is at your own risk.

## Adding or fixing a board

1. Copy a similar board's file to `boards/<new-id>.json`, or edit the board's file.
2. Fill in what you know; leave out what you don't. Say where a fact comes from with `source` (see [the model](docs/model.md)).
3. Run `scripts/test.sh` (Python 3). It checks every board and formats files the canonical way with `tools/check.py --fix`.
4. Open a pull request.

## License

Licensed under [MIT](LICENSE-MIT) or the [Apache License 2.0](LICENSE-APACHE), at your option. Logix Catalog is part of [Open Logix](https://www.openlogix.org/): free, open source tools for FPGA design.
