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

The order of resources in the map means nothing, as JSON objects are unordered: tools may keep or change it. Tools that pick a resource, such as a generator choosing a board's clock, decide by explicit rules, never by position. Order within a resource does mean something: `pins` lists are bit 0 first, or in header order.

| Type | Fields | Example |
| --- | --- | --- |
| `clock` | `pin`, `mhz` | `"clk": {"type": "clock", "pin": "35", "mhz": 12}` |
| `leds` | `pins`, `active` | `"leds": {"type": "leds", "pins": ["11", "37"], "active": "low"}` |
| `rgb_led` | `red`, `green`, `blue`, `active` | `"rgb": {"type": "rgb_led", "red": "41", "green": "39", "blue": "40", "active": "low"}` |
| `led_matrix` | `leds` (a pin per LED), `colors` (`red`, `green`, `blue`), `active` | the ButterStick's seven RGB LEDs |
| `buttons` | `pins`, `active` | `"btn": {"type": "buttons", "pins": ["10"], "active": "low"}` |
| `switches` | `pins`, `active` | like buttons |
| `uart` | `tx`, `rx`, optional `rts`, `cts` (`tx` is the FPGA's output) | `"uart": {"type": "uart", "tx": "9", "rx": "6"}` |
| `pmod` | `pins`: the 8 signal pins in header order, 1 to 4 then 7 to 10 | `"pmod1a": {"type": "pmod", "pins": ["4", "2", "47", "45", "3", "48", "46", "44"]}` |
| `header` | `pins`: every position in order, `null` for power and ground | headers that aren't PMODs |
| `unclassified` | `pins`: every FPGA pin the board wires to something no other resource describes | see Partial knowledge |

Every resource may also have:

- `io_standard`: one common name for every FPGA family (`LVCMOS33`, `LVCMOS25`, `LVCMOS18`, `LVCMOS15`, `LVCMOS12`, `LVTTL`, `LVDS`, `SSTL15`, `SSTL135`), checked against the board's FPGA family. Pin file writers translate it: `IO_TYPE` for ECP5 and Gowin, `IOSTANDARD` for Xilinx 7-series. iCE40 pin files have none, so iCE40 boards don't use it.
- `source`: where its facts come from, `{"kind": …, "ref": …}`. Kinds, strongest first: `hardware` (tried on the board), `schematic`, `maker` (the maker's docs, pin files or examples), `litex` and `amaranth` (imported from their board files; `ref` names the file and commit), `user` (reported, not yet checked).
- `requires`: what must be done for it to work (see Requirements), such as a jumper a clock needs.
- `user_notes`: warnings and missing information for users.

`active` is `high` or `low`; left out, it's unknown. An LED in a `led_matrix` lights when its pin and a color's pin are both active.

## Requirements

`requires`, on a board or on a resource, lists what must be done for it to work, each with a `type`:

| Type | Who acts | Fields | Example |
| --- | --- | --- | --- |
| `drive` | the design | `name` (a port name, unique on the board among resources and drives), `pins` (bit 0 first), `level` (`high` or `low`), optional `io_standard`, `why`, `source` | the ULX3S's `wifi_gpio0`, held high, or the ESP32 resets the board |
| `setup` | a person | `text` (what to do), optional `source` | a jumper a clock needs |

A board's requirements apply to every design for it; a resource's apply when a design uses it. Generators include a board's drives, leave out resources that need a setup (so designs work on the board as shipped), and include the drives of the resources they use. `why` and `text` are for people; tools never read them. Only these two types exist; new ones come with a real case.

## Overlap

Resources may share pins: one pin is often wired to two things, such as an LED that is also a PMOD pin, so both are listed. Within one resource, pins are unique. A design may use a pin only once: the user or a generator picks resources, or some pins of one, and tools check that no pin is picked twice. Generators pick the simplest resources that need no setup or add-on.

## Partial knowledge

A board's file lists what is known and leaves the rest unknown: a type with no resource listed is unknown, and so is a field left out, such as `active`. A board with an `unclassified` resource lists all its wired pins, so it's complete: a type it doesn't list, it doesn't have. FPGA pins wired to nothing are never listed.

## Disagreements

The file holds one value per resource, with its source, never a list of reports. When a pull request brings a different value, review keeps the better-sourced one, and git keeps the history. Importers never overwrite a resource from a stronger source; they report the difference.

## Not decided yet

- At which levels (board, resource, field) to keep user and maintainer notes. Until then, boards keep the notes they have: on variants, and `user_notes` on resources.
