# Project status and next steps

Updated at the end of every working session. Read this first, then
`docs/requirements.md`.

Last update: **2026-11-13**.

## Stopped here (2026-11-13, afternoon)

Everything up to and including the output section is drawn, verified,
committed and pushed. Power section: design note `power-section.md` v0.4,
all parts selected and in the JLCPCB library, **steps B and C drawn** (power
input and 5 V on page 9; ±15 V module, filters and ±12 V regulators on
page 10). Nothing is half-done. The next action is "Next steps" item 2,
step D.

Antonios works inside a 5-hour usage limit: work in small steps, commit after
each one, and stop with this file updated before the limit is close.

JLCPCB part search that works: open
`https://jlcpcb.com/parts/componentSearch?searchTxt=<keyword>` in the browser
pane, wait about 9 s, then read the table rows from the page. Calling the
site's search API directly in a burst gets blocked (403).

## Where we are

Phase 1, main board, schematic in progress. Requirements are at **v0.7**.

| Block | Design note | Schematic | Sheet (page) |
|---|---|---|---|
| Input jacks, mono normalling, INST/LINE relays | `input-section.md` v0.5 | drawn | `input-jacks.kicad_sch` (2) |
| LINE receivers | same | drawn | `input.kicad_sch` (3) |
| INST buffer | same | drawn | `input-inst.kicad_sch` (4) |
| Gain stages, ADC pad | same | drawn | `input-gain.kicad_sch` (5) |
| DAC gain, bypass relay | `output-section.md` v0.1, approved | drawn | `output-dac.kicad_sch` (6) |
| Volume pot header, line buffers, headphone amplifier | same | drawn | `output-pots.kicad_sch` (7) |
| Mute relays, output and headphone jacks | same | drawn | `output-jacks.kicad_sch` (8) |
| Power input, 5 V module | `power-section.md` v0.4 | drawn | `power-input.kicad_sch` (9) |
| ±15 V module, filters, ±12 V regulators | same | drawn | `power-analog.kicad_sch` (10) |
| 3.3 V regulator, mute delay circuit | same | **not drawn** | |
| Daisy Seed socket, ribbon connector to the control board | **no note yet** | not drawn | |

State of the checks: `python3 tools/schgen/verify.py` reports "netlist matches
the intended circuit". ERC gives 1 finding, expected: the label `BYPASS_RELAY` has one end (it waits
for the Daisy sheet). All supply rails now have a source. Signals still open
towards blocks that are not drawn: `INST_SW` (toggle, general ribbon),
`MUTE_SW` and `VIN_SENSE` (mute circuit), `ADC_IN_L/R`, `DAC_OUT_L/R`,
`BYPASS_RELAY` (Daisy socket).

## How the schematic is made

- The sheets are **generated** by `tools/schgen/main_board.py` (library in
  `tools/schgen/kisch.py`). Every run rewrites all `.kicad_sch` files, so
  hand edits in KiCad are lost: changes go into the script.
- `tools/schgen/verify.py` regenerates, exports KiCad's netlist and compares
  it with the connections declared in the script.
- After each step: verify, `kicad-cli sch erc`, PDF to
  `hardware/main-board/export/main-board-schematic.pdf`.
- KiCad's Schematic Editor must be closed while the script runs.

## Decisions that shape what comes next

- No digital control of analog switching. Exceptions: the bypass relay (one
  Daisy pin, `BYPASS_RELAY`). The INST/LINE toggle switches the relay coils
  directly (`INST_SW`); no mono-detection pin.
- Daisy audio pins: 16/17 in (`ADC_IN_L/R`), 18/19 out (`DAC_OUT_L/R`), 20 AGND.
- Op-amps: NE5532 everywhere except TL072 for the INST buffer and OPA1688 for
  the headphones. NE5532 stays in the gain stage U3 (decided; TL072 is the
  drop-in fallback if the gain pot rustles).
- Gain pot: two shielded 3.5 mm cables (J3, J4). Master and HP pots: one
  separate 16-wire ribbon. General ribbon: everything that is not audio.
- Power: modules preferred over converters built from parts, even if he
  buys and solders them himself; a comfortable supply, not one at the limit.
- Headphone amplifier: OPA1688, gain ×1. Upgrade path TPA6120A2 recorded in
  `output-section.md` section 8.1.
- Rough Daisy pin budget: about 15 of 31 (multiplexers 8, I2C 2, encoder 3,
  bypass relay 1, one spare for a mute). Firm table with the Daisy sheet.

## Next steps, in order

1. *(done 2026-11-13)* Second half of the output section.
2. **Power section schematic**, one small step at a time, each with netlist
   verify, ERC, PDF and commit:
   - A. *(done 2026-11-13)* parts selected, added to the library; module
     pin-outs checked against the YLPTEC datasheets in `docs/datasheet/`.
   - B. *(done 2026-11-13)* Input and 5 V: DC jack J9, PTC F1, bridge
     D9–D12, TVS D14, `VIN_SENSE` node, series diode D13, 470 µF bulk C53,
     K7805-2000R3 (PS1) with 22 µF ceramics, +5 V and GND with PWR_FLAGs.
     `VIN_DC` goes to the ±15 V module.
   - C. *(done 2026-11-13)* `power-analog.kicad_sch`: VRA1215YMD-6WR3 (PS2),
     100 µF + 2.2 µH + 100 µF filters, MC78M12 (U8) and MC79M12 (U9) with
     10 µF + 100 nF outputs, reverse diodes D15/D16, PWR_FLAGs on +12 V,
     −12 V and GNDA. The module's output common is GNDA. The 78M12 datasheet
     (onsemi MC78M00/D rev. 29) confirms 11.4–12.6 V for inputs of 14.5 V or
     more and 2.0 V typical dropout.
   - D. AMS1117-3.3 and the 3.3 V output for the control board.
   - E. Mute circuit driving `MUTE_SW`: choose comparator or supervisor and
     the coil Zener at JLCPCB, explain the circuit to Antonios before
     drawing.
   - Where AGND and GND join (at the Daisy Seed) is drawn with the Daisy
     sheet, item 3.
3. **Daisy Seed socket and control-board connectors**: official Electrosmith
   footprint, firm pin table, general ribbon pinout.
4. PWR_FLAGs / supply sources so that ERC is clean, then PCB.

## Open checks carried forward

- *(closed)* DC jack pin-out confirmed on the HRO drawing in
  `docs/datasheet/C84007.pdf`: 1 = centre pin, 2 = sleeve spring, 3 = switch
  contact.
- GNDA (isolated module output) and GND are not yet joined anywhere; they
  are joined at the Daisy Seed when its sheet is drawn.
- Pad numbering of the 2×8 header footprint against the IDC pin order (odd/even rows) before the PCB.
- NMJ6HCD2 footprint orientation against the Neutrik drawing (which row faces
  the panel) before the PCB.
- Everything marked *(measure)* in the two design notes (first-board
  acceptance test before the Seed is fitted, clicks, pot rustle, headphone
  amplifier temperature).
- The JLCPCB library repository (`~/Documents/KiCad/JLCPCB-Library/`) has no
  remote; it is committed only locally.
