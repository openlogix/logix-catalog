# Examples and boards

Open points and recommendations for frontend developers: how a frontend's
examples stay right for every board in the catalog. Nothing here is decided
for every frontend yet; Logix IDE is to follow it first. It moved here from
the Claude Doc "Open Logix: FPGA Tools Without Apio's Packages" (reviewed
2026-11-10), now obsolete.

Boards and FPGAs come in the `logix-catalog` package, which Logix Engine
downloads; each frontend ships its own examples, in its own project format,
and checks them, with no AI, against whatever catalog the engine has.

## The policy

1. **Bare minimum and blinky are generated, not shipped:** the frontend
   fills a per-family template from the board's data: the FPGA part; the
   clock pin and frequency, or the internal oscillator; the LEDs with their
   active level and any driver primitive; pin attributes such as the I/O
   standard; pins held at a level.
2. **Examples use board signals** (`clk`, `led0`, `btn1`), not pins; the
   constraints are written from the board's data when the example is used.
3. **Each example states its needs:** its signals and their assumptions
   (direction, active level, clock frequency), the family it needs (any, or
   one for vendor primitives), rough resources (LUTs, BRAM, PLLs) and the
   board file format version. A board ID is only a hint.
4. **The frontend matches the needs to the board:** compatible; compatible
   with constraints or PLL settings regenerated; or needs an update, or
   incompatible. A quick synthesis and placement on that board gives the
   final answer.
5. **CI** builds the generated blinky for every board, and checks every
   example, on each catalog change.

## Open points

- **Frontends detect a new or changed catalog** (by its version) when the
  engine's catalog changes, re-run the match for every example, and offer
  the generated bare minimum and blinky for new boards.
  *Recommendation:* required for every frontend that ships examples.
- **A daily examples package:** the frontend's CI builds its examples each
  day against that day's catalog, so a shipped package always matches a
  known catalog. *Recommendation:* a good addition; the check when an
  example is used still covers users on another catalog.
- **Examples generated offline by AI:** each records the catalog version and
  a hash of the board fields it used; the examples build compares them with
  the current catalog and flags or regenerates the example when they differ.
  *Recommendation:* yes, detect it.
