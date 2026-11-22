# Examples and boards

How a frontend's examples stay right for every board in the catalog:
recommendations for frontend developers, from what Logix IDE does (its
`spec/examples/`, since 2026-11-09; the user's decision, 2026-11-22, to
describe that here).

Boards and FPGAs come in the `logix-catalog` package, which Logix Engine
downloads; each frontend ships its own examples, in its own project format.

## The recommendation

1. **Standard examples are written by an AI agent from a spec.** A small
   set of examples every board gets (in Logix IDE: `bare-minimum`, `blinky`,
   and `serial` and `serial-debug` on boards with a UART) is described once,
   in plain words, in the frontend's repo. An AI agent writes each board's
   copy from that spec and the board's entry in the catalog, read through
   Logix Engine (`get_catalog`), including its `ai_hints`. Code generators
   were tried first and dropped: code can't read `ai_hints`, so a generator
   repeated their knowledge in its own code.
2. **Only the spec and the board.** The agent never reads existing
   examples, old versions or code that made them. When the spec and the
   board's data aren't enough to write a correct example, the fix goes into
   the catalog (a field, or an `ai_hints` line, see [model.md](model.md)) or
   into the spec, never into one board's example.
3. **Never edited by hand.** A standard example is written again, whole,
   when its spec or its board changes. Examples a frontend writes by hand
   for one board are kept apart and never touched by the agent.
4. **Every example is checked on the real engine:** it builds on its board
   with no warnings, and its testbenches pass.
5. **The catalog an example was written from is recorded** (in Logix IDE,
   `spec/examples/CATALOG.json`: each board's entry and the catalog
   version), so a later run can tell which boards changed and write only
   their examples again.

## Delivery

Logix IDE ships its examples as a package of its own
(`logix-ide-examples`), named by its remote config like Logix Engine's
packages, so a fixed or new example reaches installed copies without a new
Logix IDE release.

## Open points

- **A new catalog with changed boards** reaches users through the engine's
  remote config before the frontend's examples are written again for it. A
  frontend can compare the catalog version it wrote its examples from with
  the engine's, and say so when they differ.
