# Design

Why Logix Catalog is shaped the way it is, how it grows, and how Logix Engine uses it. The format itself is in [model.md](model.md). The design was settled with the user in a review (2026-11-07 and 2026-11-08); this document and model.md replace that review's doc.

## Goals

- **Readable.** A person opens a board's file and understands it without reading docs first.
- **Partial knowledge.** The FPGA is always fully known. Everything else is either listed, so known, or not known yet.
- **Grows in small steps.** Users, board makers, developers and importers add facts one at a time, each with where it came from.
- **Useful.** Enough to generate a blinky, a pin file or an example, and to check that a design's pins fit the board.
- **Convertible.** To and from LiteX and Amaranth board definitions, keeping everything either records about pins.

Not goals: describing the FPGA itself (`fpgas/` holds only what tools need), full schematics, or power and analog details.

## Decisions

| Decision | Why |
| --- | --- |
| A repo of its own, `logix-catalog`, and a first-level product with its own page | Board data changes more often than engine code, contributors shouldn't need the engine repo, and other projects can use the data without the engine |
| One JSON file per board, named by its ID | A contribution touches one small file; boards copy between the catalog and a project's `boards/` folder as files |
| One schema, `logix-board-v1.json`; custom boards are folders of the same files | One format everywhere; no wrapper files |
| `resources`, a map from port name to a typed resource | Amaranth's and LiteX's term, so imports map 1:1; names are unique because they're port names |
| Each type with its own fields (`pin`, `red`, `tx`, `leds`, `colors`) | A reader never decodes a pin list by position |
| One pin gives a plain port, several a vector | Natural for beginners; blinkies are per board anyway |
| Resources may share pins; designs may not | A pin is often wired to two things, such as an LED on a PMOD pin |
| `unclassified` makes a board complete | Lists every wired pin no other resource covers, so absence can be stated without a marker per type |
| `requires` on boards and resources, of two types: `drive` (the design) and `setup` (a person) | Generators can tell what a design must include and what needs a jumper, without reading notes; more types only with a real case (the user's idea, 2026-11-08) |
| One common `io_standard` name, translated per FPGA family | Board files stay family-neutral; the checker knows each family's set |
| One value and one `source` per resource; review settles disagreements | No history of reports to manage; git keeps the history |
| A board's USB device is board data; matching stays the engine's | Useful facts about the board, while match criteria stay internal to the engine |
| MIT or Apache 2.0, like every Logix repo | MIT lets GPL-2.0 projects use the data, Apache 2.0 gives a patent grant |
| Contributions through commits and pull requests | Standard review, nothing special to learn |
| Motto: "Every FPGA board, described once." | |

## Sources and importing

Every resource can say where it came from (`source`, see model.md). Kinds rank, strongest first: `hardware`, `schematic`, `maker`, `litex` and `amaranth`, `user`. Importers never overwrite a resource from a stronger source; they report the difference instead.

LiteX's and Amaranth's board files cover 57 of the 81 boards (LiteX 51, Amaranth 35; checked 2026-11-08), so importing fills most resources. Both describe boards in Python, so importers are Python scripts in `tools/` (planned). The mapping:

| LiteX or Amaranth | Our type |
| --- | --- |
| `clk12`, `clk25`, `clk100` (frequency from the name or the period) | `clock` |
| `user_led`, `led` (by index); Amaranth's `invert` or `PinsN` gives `active: low` | `leds` |
| `rgb_led` with `r`, `g`, `b` | `rgb_led` |
| `user_btn`, `button` | `buttons` |
| `user_sw`, `switch` | `switches` |
| `serial`, `uart` with `tx`, `rx` | `uart` |
| `pmod` connectors (12 positions) | `pmod` (the 8 signal pins) |

Names the table doesn't know are reported, never guessed. LiteX rarely records LED polarity, so where only LiteX has a board, `active` stays unknown. Export, writing an Amaranth `Platform` class or LiteX `_io` and `_connectors` lists from a board's file, comes later, when someone needs it.

## Logix Engine and the catalog

Contributors change boards here, never in the engine repo. Every engine build embeds a catalog, so the engine's startup stays offline. Planned:

- **Release builds:** the engine repo pins a catalog release (a dated tag), as it pins toolchain packages, and builds it in. `get_engine_info` reports the catalog's version, and frontends show it, such as in the Logix IDE's System Info.
- **Local builds:** `LOGIX_ENGINE_DEV_CATALOG=<local clone>` at build time embeds a local checkout instead, and `get_engine_info` reports it as local. Edit a board, rebuild the engine, try it in the IDE.
- **Custom boards:** requests name a folder of board files (`custom_boards_folder`), read with the same code as the catalog.
- **Later, updates without a new engine:** the engine installs a newer catalog release into its engine folder, like a toolchain package, only when a host asks: it never downloads at startup or upgrades silently. A host can't pick a catalog version; the engine uses the one it has.
- The engine keeps the code that reads and checks the catalog, and drops its own `catalog/` folder.
