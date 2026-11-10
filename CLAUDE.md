# CLAUDE.md

Guidance for Claude working in this repo. Shared Open Logix rules (products, principles, brand, license, repo naming, environment variable names) live in the website repo's `CLAUDE.md`; this file holds Logix Catalog's own.

## What this is

Logix Catalog ("Every FPGA board, described once.") is the open catalog of FPGA boards: one JSON file per board in `boards/`, the FPGAs in `fpgas/`, one file per FPGA family. Logix Engine builds a pinned catalog release into its binary and serves it. The shared rule (website repo's `CLAUDE.md`, 2026-11-08): every Logix product, script and agent gets catalog data only through the engine's API; only this repo's own maintenance (the checker, importers, tests and CI) reads and writes the files directly. For everyone else the engine's API is the intended, supported interface, not enforced: the data stays free to use and copy, and reading the files directly is at the reader's own risk (`README.md`, `boards/README.md`, `fpgas/README.md` say so; write "intended", never "allowed"). The board file format stays public for writing boards (custom boards and contributions). Contributors add and fix boards here, never in the engine repo.

[`docs/model.md`](docs/model.md) is the source of truth for the format, and [`docs/design.md`](docs/design.md) for the decisions behind it, importing, and how the engine uses the catalog. Read them before changing the schemas, the checker or the data, and update them in the same change. They replace the design review doc (2026-11-08), which is obsolete.

## Layout and commands

- **Docs site** (2026-11-10, as Logix IDE's and Logix Engine's): `docs/` is published with MkDocs Material at www.openlogix.org/logix-catalog/ (`mkdocs.yml`; `docs/index.md`, the home page, follows `README.md`; `docs/requirements.txt` pins the tools, separate from the checker's `requirements.txt`) by `.github/workflows/publish-docs.yaml` (`mkdocs build --strict`: a broken link fails it). Links in `docs/` stay inside it or are full URLs. The product page, www.openlogix.org/catalog/, stays in the website repo.

- `boards/<id>.json`: one board each (`$schema` logix-board-v1). `fpgas/<family>.json` (`ice40`, `ecp5`, `gw1n`, `gw2a`, `gw5a`, `artix7`, `spartan7`, `zynq7000`; the families on the chips' datasheets): FPGAs by ID; the file's name gives their family, and an ID is in one file only. Boards never name a family or a toolchain: a board's family is its FPGA's (decided 2026-11-08).
- `schemas/logix-board-v1.json`: one board's file, the only board schema (custom boards are folders of the same files; the user's decision, 2026-11-08). `schemas/logix-fpgas-<schema>-v1.json` (`ice40`, `ecp5`, `gowin`, `openxc7`): the FPGA files' schemas, one per set of fields, shared by the families that have the same ones and named after the toolchain that builds them; schema names are the only place the catalog names toolchains (2026-11-08). `tools/check.py`'s `FAMILIES` lists each family's schema and part number prefixes. Hand-written JSON Schema 2020-12; this repo owns them. The website serves copies at `www.openlogix.org/schemas/`: after a change, copy them to the website repo's `docs/schemas/` and push it (it goes live). Until the first release it changes without a new version.
- `tools/check.py`: checks every board and FPGA file against its schema, then the rules the schemas can't express (FPGA IDs exist and are in one file only, part numbers fit their file's family, no pin twice in a resource, I/O standards valid for the FPGA family, unique variant selectors, known `${…}` variables, flash first), then the canonical format (two-space indents; an object or array that fits in 100 columns on one line; `ai_hints` last in its board or resource). `--fix` rewrites files in the canonical format.
- `tests/test_check.py`: the checker's tests, a board breaking each rule.
- **Before committing, run `scripts/test.sh`.** It makes `.venv` with `requirements.txt` (jsonschema, pinned) on first use. CI (`.github/workflows/test.yaml`) runs the same script.

## Rules

- Keep facts true: every value comes from a source (the board's maker, its schematic, LiteX or Amaranth board files, hardware tests). Record the source in `source` for new facts. Never guess pins or polarity; leave unknowns out.
- Boards that can't be bought anymore, for some time, are dropped (the user's rule).
- Examples and generated designs use only a board's default configuration (no jumpers or add-ons) unless very explicit; resources that need a jumper have a `setup` requirement, and pins every design must drive are a board's `drive` requirements (`requires`, docs/model.md).
- `ai_hints` (boards and resources; 2026-11-09): only what the structured data can't express, led by a fact about the board (where it comes from decides, not how many boards share it), with at most a short phrase of context naming the FPGA feature, and no how-to. The rules are in docs/model.md, "AI hints".
- **The canonical board** (the website repo's `CLAUDE.md` owns the rule, 2026-11-10): `icesugar-1-5` (iCESugar v1.5) is kept as complete and accurate as possible: every pin it wires (its `unclassified` resource makes the list complete), each from its schematic, its maker's files or a hardware test. The checker and tools treat it like every other board. Still to check on a real board: whether jumpers J1 (clock), J5 (UART) and J6 (RGB LED) come fitted; any that don't become `setup` requirements. The 6-pin PMOD4's power positions (5 GND, 6 3.3 V) also need checking.
- Breaking format changes are fine until the first release; after it, only additions.
- Releases: dated tags (`yyyy-mm-dd`), not set up yet; the engine will pin one.

## Next steps

- Importers from LiteX and Amaranth board files (Python, in `tools/`), filling resources with `source` set; they cover 57 of the 81 boards.
