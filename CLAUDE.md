# CLAUDE.md

Guidance for Claude working in this repo. Shared Open Logix rules (products, principles, brand, license, repo naming, environment variable names) live in the website repo's `CLAUDE.md`; this file holds Logix Catalog's own.

## What this is

Logix Catalog ("Every FPGA board, described once.") is the open catalog of FPGA boards: one JSON file per board in `boards/`, the FPGAs in `fpgas.json`. Logix Engine builds a pinned catalog release into its binary; other projects can use the data without the engine. Contributors add and fix boards here, never in the engine repo.

[`docs/model.md`](docs/model.md) is the source of truth for the format. Read it before changing the schemas, the checker or the data, and update it in the same change. The design was settled with the user in a review doc (2026-11-08); its decisions are all in `docs/model.md`.

## Layout and commands

- `boards/<id>.json`: one board each (`$schema` logix-board-v1). `fpgas.json`: FPGAs by ID.
- `schemas/logix-board-v1.json` (one board's file) and `schemas/logix-boards-v2.json` (custom boards files: a map from board ID to the same board objects). Hand-written JSON Schema 2020-12; this repo owns them. The website serves copies at `www.openlogix.org/schemas/`: after a change, copy them to the website repo's `docs/schemas/` and push it (it goes live). Until the first release they change without a new version.
- `tools/check.py`: checks every board against the schema, then the rules the schema can't express (FPGA IDs exist, no pin twice in a resource, I/O standards valid for the FPGA family, unique variant selectors, known `${…}` variables, flash first), then the canonical format (two-space indents; an object or array that fits in 100 columns on one line). `--fix` rewrites files in the canonical format.
- `tests/test_check.py`: the checker's tests, a board breaking each rule.
- **Before committing, run `scripts/test.sh`.** It makes `.venv` with `requirements.txt` (jsonschema, pinned) on first use. CI (`.github/workflows/test.yaml`) runs the same script.

## Rules

- Keep facts true: every value comes from a source (the board's maker, its schematic, LiteX or Amaranth board files, hardware tests). Record the source in `source` for new facts. Never guess pins or polarity; leave unknowns out.
- Boards that can't be bought anymore, for some time, are dropped (the user's rule).
- Examples and generated designs use only a board's default configuration (no jumpers or add-ons) unless very explicit; resources that need a jumper say so in `user_notes`.
- Breaking format changes are fine until the first release; after it, only additions.
- Releases: dated tags (`yyyy-mm-dd`), not set up yet; the engine will pin one.

## Next steps

- Logix Engine: read boards from this repo's format, build a pinned release in (local builds from a clone via `LOGIX_ENGINE_DEV_CATALOG`), report the catalog version in `get_engine_info`, drop its own `catalog/`; the Logix IDE shows the catalog version in System Info.
- Importers from LiteX and Amaranth board files (Python, in `tools/`), filling resources with `source` set; they cover 57 of the 81 boards.
