# CLAUDE.md

Guidance for Claude working in this repo. Shared Open Logix rules (products, principles, brand, license, repo naming, environment variable names) live in the website repo's `CLAUDE.md`; this file holds Logix Catalog's own.

## What this is

Logix Catalog ("Every FPGA board, described once.") is the open catalog of FPGA boards: one JSON file per board in `boards/`, the FPGAs in `fpgas/`, one file per FPGA family. Logix Engine builds a pinned catalog release into its binary and serves it: every other tool, script or agent reads the catalog only through the engine's API, never these files (the shared rule, website repo's `CLAUDE.md`, 2026-11-08). Only this repo's own maintenance (the checker, importers, tests and CI) reads and writes the files directly. The board file format stays public for writing boards (custom boards and contributions). Contributors add and fix boards here, never in the engine repo.

[`docs/model.md`](docs/model.md) is the source of truth for the format, and [`docs/design.md`](docs/design.md) for the decisions behind it, importing, and how the engine uses the catalog. Read them before changing the schemas, the checker or the data, and update them in the same change. They replace the design review doc (2026-11-08), which is obsolete.

## Layout and commands

- `boards/<id>.json`: one board each (`$schema` logix-board-v1). `fpgas/<family>.json` (`ice40`, `ecp5`, `gw1n`, `gw2a`, `gw5a`, `artix7`, `spartan7`, `zynq7000`; the families on the chips' datasheets): FPGAs by ID; the file's name gives their family, and an ID is in one file only. Boards never name a family or a toolchain: a board's family is its FPGA's (decided 2026-11-08).
- `schemas/logix-board-v1.json`: one board's file, the only board schema (custom boards are folders of the same files; the user's decision, 2026-11-08). `schemas/logix-fpgas-<schema>-v1.json` (`ice40`, `ecp5`, `gowin`, `openxc7`): the FPGA files' schemas, one per set of fields, shared by the families that have the same ones and named after the toolchain that builds them; schema names are the only place the catalog names toolchains (2026-11-08). `tools/check.py`'s `FAMILIES` lists each family's schema and part number prefixes. Hand-written JSON Schema 2020-12; this repo owns them. The website serves copies at `www.openlogix.org/schemas/`: after a change, copy them to the website repo's `docs/schemas/` and push it (it goes live). Until the first release it changes without a new version.
- `tools/check.py`: checks every board and FPGA file against its schema, then the rules the schemas can't express (FPGA IDs exist and are in one file only, part numbers fit their file's family, no pin twice in a resource, I/O standards valid for the FPGA family, unique variant selectors, known `${…}` variables, flash first), then the canonical format (two-space indents; an object or array that fits in 100 columns on one line). `--fix` rewrites files in the canonical format.
- `tests/test_check.py`: the checker's tests, a board breaking each rule.
- **Before committing, run `scripts/test.sh`.** It makes `.venv` with `requirements.txt` (jsonschema, pinned) on first use. CI (`.github/workflows/test.yaml`) runs the same script.

## Rules

- Keep facts true: every value comes from a source (the board's maker, its schematic, LiteX or Amaranth board files, hardware tests). Record the source in `source` for new facts. Never guess pins or polarity; leave unknowns out.
- Boards that can't be bought anymore, for some time, are dropped (the user's rule).
- Examples and generated designs use only a board's default configuration (no jumpers or add-ons) unless very explicit; resources that need a jumper have a `setup` requirement, and pins every design must drive are a board's `drive` requirements (`requires`, docs/model.md).
- Breaking format changes are fine until the first release; after it, only additions.
- Releases: dated tags (`yyyy-mm-dd`), not set up yet; the engine will pin one.

## Next steps

- Importers from LiteX and Amaranth board files (Python, in `tools/`), filling resources with `source` set; they cover 57 of the 81 boards.
