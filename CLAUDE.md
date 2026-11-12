# CLAUDE.md — Plug & Roll

Instructions for Claude when working in this repository. Read this file and
`docs/requirements.md` at the start of every session.

## Project

Plug & Roll is a desktop stereo audio multi-effect device built around a
**Daisy Seed Rev 5 (codec WM8731)**. It is a prototype for personal use.
Hardware is designed in **KiCad 10** (macOS) and fabricated and assembled at **JLCPCB**.
On macOS, `kicad-cli` is at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
Firmware is C++ on **libDaisy / DaisySP**.

`docs/requirements.md` is the **single source of truth**. If a request
conflicts with it, point out the conflict before doing the work. When a
decision changes, update `docs/requirements.md` in the same change.

## About the owner

- Antonios is an acoustic and DSP engineer. He is **not** experienced in
  embedded hardware design or low-level real-time programming.
- Be objective and strict. Do not agree with something that is wrong. Act as a
  senior engineer and mentor: explain the reasoning behind every hardware
  decision (why this topology, why this part, what the trade-off is).
- DSP theory can be discussed at expert level. Electronics and embedded topics
  need explanation.
- He gives direction at a high level. Claude owns the detailed electronics
  decisions, but every decision is explained in plain terms and approved by him
  before it goes into a schematic. Present choices as: what it does, why, what
  the alternative would cost.

## Repository layout

```
docs/                    requirements, decisions, design notes, datasheets notes
hardware/
  main-board/            KiCad project: power, analog I/O, bypass, HP amp, Daisy Seed (4-layer)
  control-board/         KiCad project: pots, muxes, buttons, encoder, LEDs (2-layer)
  front-panel/           KiCad project: cosmetic front panel PCB (LED windows, graphics)
firmware/                Daisy Seed firmware (libDaisy / DaisySP)
tools/                   helper scripts (BOM checks, exports)
```

KiCad projects are created by Antonios in KiCad 10 (File → New Project), so
the project files are in KiCad's native format. Claude does not generate a
`.kicad_pro` from scratch; it edits the projects that exist. When a new board
phase starts, ask him to create the project and tell him the exact folder and
name. `hardware/main-board/` is created first.

## Hardware rules (mandatory)

1. **Every SMD part has an LCSC part number** in a symbol field named `LCSC`
   (value `Cxxxxx`). Check JLCPCB stock and Basic/Extended status before
   placing a part. No part goes into a schematic without this.
2. **Basic parts first.** Extended parts only where audio quality depends on
   them. Reuse the same part (e.g. one op-amp type) wherever possible.
3. Passives in **0603**.
4. Symbols, footprints and 3D models come from the LCSC/EasyEDA library via
   `easyeda2kicad` and go into Antonios's **personal global JLCPCB library**,
   shared by all his projects:
   - Location: `~/Documents/KiCad/JLCPCB-Library/` (symbols, footprints,
     3D models), registered once in KiCad's global library tables through the
     path variable `JLCPCB_LIB`.
   - If it does not exist yet, create it, register it, and explain to
     Antonios what was done.
   - Before downloading a part, check whether it is already in the library.
   - Every library part keeps its `LCSC` field.
   - KiCad stores a copy of every used symbol in the schematic and every
     footprint in the PCB, so this project still opens if the library changes.
   - Recommend putting the library under its own git repository.
5. THT/panel parts (pots, jacks, buttons, encoder, relay, DC jack, headers) are
   hand-soldered, but still get an LCSC number so they are ordered together.
6. Daisy Seed: 2× female headers 1×20, 2.54 mm, on the **bottom side** of the
   main board; footprint spacing from the official Electrosmith footprint.
   Keep BOOT/RESET reachable from the removable bottom plate and keep space for
   the USB extension plug.
7. Run **ERC** (schematic) and **DRC** (PCB, JLCPCB capabilities) with
   `kicad-cli` before saying a design step is done. Report every remaining
   warning with an explanation.
8. Before an order: BOM + CPL with `kicad-jlcpcb-tools`, check rotations in the
   JLCPCB 3D preview.
9. Never invent part values, pinouts or datasheet numbers. If a value comes
   from a datasheet, cite which one. If it must be measured, say so.

## Collaboration rules (KiCad files)

- **Never edit a `.kicad_sch` / `.kicad_pcb` that Antonios has open with
  unsaved changes.** Before every edit, tell him exactly what to close:
  - schematic edits → save and close the **Schematic Editor** window;
  - PCB edits → save and close the **PCB Editor** window;
  - project settings or library table changes (`.kicad_pro`,
    `sym-lib-table`, `fp-lib-table`, global library tables) → close the
    **whole project / KiCad**.
  The KiCad Project Manager window can otherwise stay open. Wait for his
  confirmation, then edit. Afterwards, tell him which window to reopen.

## Guiding Antonios through setup and manual steps

He is new to this workflow. Whenever a step needs him, say **what** to do,
**where** (exact menu path or window), and **why**, at the moment it is
needed, not in advance. Known manual steps:
- Approving tool installs and commands Claude asks to run.
- **JLCPCB Tools plugin** (needed in the ordering phase, not before): KiCad →
  Plugin and Content Manager → search "JLCPCB" → Install. Remind him when the
  first PCB approaches ordering.
- Opening/closing KiCad windows as described above.
- Measurements on real hardware (e.g. Daisy Seed full-scale level).
- Make small, reviewable changes. After each change, summarize what changed
  and why, and export a PDF/SVG of the affected sheet when it helps review.
- **Git:** propose a commit before and after every non-trivial change. Do not
  commit or push without his approval. Commit messages describe the design
  change, not just the files.

## Firmware rules

- 48 kHz, 32-bit float, block size about 48 samples.
- Audio callback: **no allocation, no blocking calls, no I/O, no logging**.
  Controls, buttons and LEDs are handled outside the callback.
- All parameters are smoothed. Effect On/Off and mode switches use short
  crossfades (about 10 ms). Delay and reverb keep their trails.
- Oversampling only in nonlinear stages.
- Measure CPU load with all effects on; target below 75–80%.

## Out of scope (do not add unless asked)

MIDI, presets, battery power, certification work, physical modeling,
encoders other than the delay time encoder.
