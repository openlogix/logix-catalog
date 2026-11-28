# The board model

How a board is described in Logix Catalog. The schemas in `schemas/` follow this document; `tools/check.py` checks what they can't.

## A board's file

Each board is one file, `boards/<id>.json`. The ID is the file name: lowercase letters, digits and dashes. A board is its name: anything that changes its pins is another board, and each FPGA size is its own board.

| Field | Required | What it holds |
| --- | --- | --- |
| `$schema` | yes | `https://www.openlogix.org/schemas/logix-board-v1.json` |
| `name` | yes | The board's name for people, such as "iCEBreaker" |
| `fpga_id` | yes | The FPGA, an ID from `fpgas/`. The FPGA is always fully known |
| `variants` | yes | The ways to program the board; the first is the default (see Variants) |
| `requires` | no | What every design for the board must do (see Requirements) |
| `resources` | no | What the board wires to FPGA pins, a map from name to resource (see Resources) |
| `ai_hints` | no | Hints for designs for the whole board (see AI hints); always the last field |

Custom boards use the same layout: a folder of `<id>.json` files, each one board in this format, such as a project's `boards/` folder that a host passes to Logix Engine as `custom_boards_folder`. A custom board with a catalog board's ID replaces it. A board copies between a project and the catalog as a file, name and all, so a custom board becomes a contribution by moving its file into a pull request.

`fpgas/<family>.json`, one file per FPGA family, maps each FPGA ID to its facts; the file's name gives the FPGA's family, and an ID is in one file only. A board's family is its FPGA's, so board files never name one. The families are the names on the chips and their datasheets:

| File | Family | Part numbers | Schema |
| --- | --- | --- | --- |
| `ice40.json` | iCE40 | ICE40…, ICE5… | `ice40` |
| `ecp5.json` | ECP5 | LFE5… | `ecp5` |
| `gw1n.json` | GW1N (LittleBee) | GW1N… | `gowin` |
| `gw2a.json` | GW2A (Arora) | GW2A… | `gowin` |
| `gw5a.json` | GW5A (Arora V) | GW5A… | `gowin` |
| `artix7.json` | Artix-7 | XC7A… | `openxc7` |
| `spartan7.json` | Spartan-7 | XC7S… | `openxc7` |
| `zynq7000.json` | Zynq-7000 | XC7Z… | `openxc7` |

Each file starts with its schema, `"$schema": "https://www.openlogix.org/schemas/logix-fpgas-<schema>-v1.json"`, which lists its FPGAs' fields. Families whose FPGAs have the same fields share a schema, named after the toolchain that builds them: schema names are the one place the catalog names toolchains (Logix Engine maps each family to its toolchain). The facts: `part_number`, `size`, the toolchain's device names, and `jtag_idcode` where the board is programmed over JTAG. Nothing the family implies is repeated per FPGA. It has every FPGA the toolchains support, so boards never add FPGAs.

## Variants

Each variant is one way to program the board:

| Field | What it holds |
| --- | --- |
| `selector` | `{"connection": …, "memory": …}`. Connection: `usb`, `bootloader`, `ft2232h`, `ft232h`, `cmsis-dap`, `usb-blaster` or `unspecified`. Memory: `flash` or `ram`. No two variants of a board share a selector |
| `programmer` | `openfpgaloader`, `iceprog`, `dfu-util` or `icesprog` |
| `args` | The programmer's arguments, with `${VID}`, `${PID}`, `${BUS}`, `${DEV}`, `${SERIAL_NUM}`, `${USB_PATH}` and `${BITSTREAM}` |
| `usb` | The USB device the board is programmed through: `vid`, `pid`, and when known `product_regex`, `release` (bcdDevice) and `serial_regex`. These are facts about the board; how a tool matches devices to boards is its own |
| `tested` | Whether programming this way is known to work |
| `user_notes`, `maintainer_notes` | Optional notes for users, and for maintainers (where settings come from and why they changed) |

When a board has a variant that writes flash, the first variant writes flash.

## Resources

`resources` maps each name to a resource. The name is the port name a design uses, a Verilog identifier, so it's unique on the board. One pin gives a plain port and several a vector, bit 0 first: a one-LED board's `led` gives `output led`, an eight-LED board's `leds` gives `output [7:0] leds`.

The order of resources in the map means nothing, as JSON objects are unordered: tools may keep or change it. Tools that pick a resource, such as a generator choosing a board's clock, decide by explicit rules, never by position. Order within a resource does mean something: `pins` lists are bit 0 first, or in header order (a PMOD's).

| Type | Fields | Example |
| --- | --- | --- |
| `clock` | `pin`, `mhz` | `"clk": {"type": "clock", "pin": "35", "mhz": 12}` |
| `leds` | `pins`, `active` | `"leds": {"type": "leds", "pins": ["11", "37"], "active": "low"}` |
| `rgb_led` | `red`, `green`, `blue`, `active` | `"rgb": {"type": "rgb_led", "red": "41", "green": "39", "blue": "40", "active": "low"}` |
| `led_matrix` | `leds` (a pin per LED), `colors` (`red`, `green`, `blue`), `active` | the ButterStick's seven RGB LEDs |
| `buttons` | `pins`, `active` | `"btn": {"type": "buttons", "pins": ["10"], "active": "low"}` |
| `switches` | `pins`, `active` | like buttons |
| `uart` | `tx`, `rx`, optional `rts`, `cts` (`tx` is the FPGA's output), optional `usb_interface` (see below) | `"uart": {"type": "uart", "tx": "9", "rx": "6"}` |
| `pmod` | `pins`: the 8 signal pins in header order, 1 to 4 then 7 to 10 | `"pmod1a": {"type": "pmod", "pins": ["4", "2", "47", "45", "3", "48", "46", "44"]}` |
| `header` | `positions`: what each position is wired to, by its ID; optional `grid` (see Headers) | headers that aren't PMODs |
| `unclassified` | `pins`: every FPGA pin the board wires to something no other resource describes | see Partial knowledge |

**Addressable LEDs aren't `rgb_led`.** An `rgb_led` is three LEDs in one package, a pin each, lit by the pin's level. An addressable LED (WS2812, SK6812, "NeoPixel" and the like) has one data pin and its own controller: the FPGA sends it colors over a timed serial protocol, often to several LEDs in a chain. So it's a different type, which doesn't exist yet: no board here lists one (2026-11-24). Until it does, a board's addressable LED is an `unclassified` pin, with a `user_notes` line saying what it is, never an `rgb_led` (designs for an `rgb_led`, such as Logix IDE's `rgb-fade` example, would drive it wrongly).


### Headers

A `header` describes a connector that isn't a standard PMOD: where each FPGA pin is on it, and what its other positions are. It isn't a design port: designers pick its pins and name their own ports.

`positions` maps each position's ID, as the board or its schematic marks it (`1`, `1a`, `A10`; letters, digits, `-` and `_`), to exactly one of:

| Form | Means |
| --- | --- |
| `{"pin": "28"}` | an FPGA pin |
| `{"power": "3.3V"}` | a supply or ground: `GND`, `VIN` or a voltage such as `3.3V` or `5V` |
| `{"net": "S1"}` | anything else on the board, named as its schematic names it |
| `{"unconnected": true}` | wired to nothing |
| `{"unknown": true}` | not known yet |

A position to keep clear of, such as one wired to the FPGA's configuration, is a `net`, with the warning in `user_notes`. The map has no order: tools show positions in natural ID order (`2` before `10`, `1a` before `1b`).

`grid`, optional, is how the positions are arranged, when the IDs don't make it clear: rows of IDs as seen from the component side, with the board edge nearest the header at the bottom, rows from that edge inward and each left to right; `null` for a gap. Every position is in it once, and its rows are of one length. The iCESugar v1.5's PMOD4, numbered like an IC:

```json
"pmod4": {
  "type": "header",
  "positions": {
    "1": {"power": "3.3V"}, "2": {"power": "GND"},
    "3": {"net": "S1"}, "4": {"net": "S2"}, "5": {"net": "S3"}, "6": {"net": "S4"},
    "7": {"pin": "21"}, "8": {"pin": "20"}, "9": {"pin": "19"}, "10": {"pin": "18"},
    "11": {"power": "GND"}, "12": {"power": "3.3V"}
  },
  "grid": [["1", "2", "3", "4", "5", "6"], ["12", "11", "10", "9", "8", "7"]]
}
```

Every resource may also have:

- `io_standard`: one common name for every FPGA family (`LVCMOS33`, `LVCMOS25`, `LVCMOS18`, `LVCMOS15`, `LVCMOS12`, `LVTTL`, `LVDS`, `SSTL15`, `SSTL135`), checked against the board's FPGA family. Pin file writers translate it: `IO_TYPE` for ECP5 and Gowin, `IOSTANDARD` for Xilinx 7-series. iCE40 pin files have none, so iCE40 boards don't use it.
- `source`: where its facts come from, `{"kind": …, "ref": …}`. Kinds, strongest first: `hardware` (tried on the board), `schematic`, `maker` (the maker's docs, pin files or examples), `litex` and `amaranth` (imported from their board files; `ref` names the file and commit), `user` (reported, not yet checked).
- `requires`: what must be done for it to work (see Requirements), such as a jumper a clock needs.
- `user_notes`: warnings and missing information for users.
- `ai_hints`: hints for designs that use the resource (see AI hints); always its last field.

A `uart` wired to the board's own USB chip, the serial port a computer sees over the board's USB cable, may have `usb_interface`: the USB interface that carries it on the board's USB device (the one its variants' `usb` filters match), such as `1` for an FTDI chip's second channel, whose first programs the board (decided 2026-11-19, for the Serial Monitor). With it, Logix Engine finds the board's serial port by itself, even when the computer lists several for the board. Left out when the chip has a single serial port (the engine then takes the only one) or when it isn't known; a UART on a header, with no USB chip, has none. Its `user_notes` still say, for people, which port it is.

**For the debugger.** Logix Engine's in-design debugger talks to the design over a UART, and finds it in the board's file: a `uart` resource named `uart` (debug files name it, `uplink = { kind = "uart", resource = "uart" }`, and Logix IDE's Debug writes that by default), wired to the board's own USB serial bridge, with `usb_interface` when the bridge's chip has several, and the board's `clock` with its `mhz`. A board without them can still be debugged with a USB serial adapter on two free pins, so neither is required; adding a bridge's `uart` saves users that. When the bridge only works at a slow rate (below 115200 baud), the resource's `ai_hints` say so. Logix Engine's [debugger docs](https://www.openlogix.org/logix-engine/debugger/) (Boards) list which boards have them.

`active` is `high` or `low`; left out, it's unknown. An LED in a `led_matrix` lights when its pin and a color's pin are both active.

## Requirements

`requires`, on a board or on a resource, lists what must be done for it to work, each with a `type`:

| Type | Who acts | Fields | Example |
| --- | --- | --- | --- |
| `drive` | the design | `name` (a port name, unique on the board among resources and drives), `pins` (bit 0 first), `level` (`high` or `low`), optional `io_standard`, `why`, `source` | the ULX3S's `wifi_gpio0`, held high, or the ESP32 resets the board |
| `setup` | a person | `text` (what to do), optional `source` | a jumper a clock needs |

A board's requirements apply to every design for it; a resource's apply when a design uses it. Generators include a board's drives, leave out resources that need a setup (so designs work on the board as shipped), and include the drives of the resources they use. `why` and `text` are for people; tools never read them. Only these two types exist; new ones come with a real case.

## AI hints

`ai_hints`, on a board or a resource, is text for whoever writes designs for the board, mainly AI agents, and people too: what its structured fields can't express. Logix Engine returns the hints with the board, unchanged; tools never read them, like `why` and `text`. Example, the UPduino v3.1's RGB LED:

```json
"ai_hints": [
  "Wired to the FPGA's RGB LED driver pads: red RGB2, green RGB0, blue RGB1.",
  "Drive it through SB_RGBA_DRV, the iCE40 UltraPlus's RGB LED driver cell (sink only)."
]
```

What goes in them:

- **Only when the structured data isn't enough.** Anything a field can hold goes in a field, or in a new field added with its first real case, never in a hint. Facts the structured data already implies, such as a board with no clock that works as shipped, aren't repeated.
- **The board's fact leads.** A hint says something true of this board: how its maker wired or built it, from its schematic, its maker or a test on it. To tell a board fact from an FPGA fact, ask where it comes from, not how many boards share it: boards often share wiring (one maker's boards, clones), but a fact from the FPGA's datasheet, true for any board with that FPGA and package, is an FPGA fact.
- **Context for people is welcome, briefly.** A short phrase may name the FPGA feature involved and say what it is ("SB_RGBA_DRV, the iCE40 UltraPlus's RGB LED driver cell"), so a reader who doesn't know the datasheet understands the hint. It must be true on every board it's copied to.
- **No how-to.** No settings, steps or values for using the FPGA's features, such as driver currents or which input level lights an LED: those are datasheet knowledge that AI agents have, and copies on many boards go wrong unchecked. Nothing that holds for every board with the FPGA, such as its internal oscillator.
- **Advice, not orders:** hints are written as facts and suggestions to weigh, never as instructions to an agent.
- **A list of lines:** each a non-empty single line of at most 90 characters, so it fits on one line of the file, and the list is never empty; with nothing to say, the field is left out.
- **Last:** always the last field of its board or resource, so it reads as a note on what's above it. `tools/check.py --fix` moves it there.
- Only on boards and resources: variants are about programming, requirements have `why` and `text`, and the FPGA files hold facts, not hints.

## Overlap

Resources may share pins: one pin is often wired to two things, such as an LED that is also a PMOD pin, so both are listed. Within one resource, pins are unique. A design may use a pin only once: the user or a generator picks resources, or some pins of one, and tools check that no pin is picked twice. Generators pick the simplest resources that need no setup or add-on.

## Partial knowledge

A board's file lists what is known and leaves the rest unknown: a type with no resource listed is unknown, and so is a field left out, such as `active`. A board with an `unclassified` resource lists all its wired pins, so it's complete: a type it doesn't list, it doesn't have. FPGA pins wired to nothing are never listed.

## Disagreements

The file holds one value per resource, with its source, never a list of reports. When a pull request brings a different value, review keeps the better-sourced one, and git keeps the history. A resource from a weaker source never replaces one from a stronger source.

## Not decided yet

- At which levels (board, resource, field) to keep user and maintainer notes. Until then, boards keep the notes they have: on variants, and `user_notes` on resources. (AI hints are settled: on boards and resources, see AI hints.)
