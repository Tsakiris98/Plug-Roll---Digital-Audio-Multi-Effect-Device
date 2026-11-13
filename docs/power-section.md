# Power Section — Design Note (v0.3, 2026-11-13)

Status: **direction approved on 2026-11-13; nothing in the schematic yet.**
Antonios's decisions: ready-made converter modules instead of converters
built from parts, even from a lesser-known brand, and even if he has to buy
and solder them himself; a supply that works comfortably, not at the limit;
the adapter is whatever the design really needs (the 9–15 V range in the
requirements was a guess). Changes from v0.1: sections 2 to 6 and 9 rewritten
around two modules and a 12 V adapter. Numbers marked *(estimate)* are my
allowances, not datasheet values; numbers marked *(measure)* are confirmed on
the first board. Datasheets marked "to read" are read before the schematic.

## 1. What the power supply has to deliver

From `docs/requirements.md` v0.6:

- DC jack 5.5 × 2.1 mm, **12 V DC adapter, either polarity**, resettable
  fuse, transient protection (requirements v0.7; was 9–15 V).
- **±12 V for the analog section**, each rail inside ±5 % (never above
  12.6 V): the protection of the Daisy ADC input depends on it. DC-DC
  converter, LC filter, then linear regulators.
- **5 V** for the relay coils (about 105 mA) and for the Daisy Seed (its VIN
  accepts 4–17 V, Daisy Seed datasheet v1.0.5, Table 1).
- **3.3 V** for LEDs and logic on the control board, so the Seed's own
  regulator is not loaded.
- Outputs muted at power-up and power-down, by an analog circuit (line
  `MUTE_SW` of the output section).
- One star ground; analog and digital return currents kept apart.

## 2. Power budget

| Consumer | Rail | Current | Source of the number |
|---|---|---|---|
| 4× NE5532 (U1, U3, U4, U5) | ±12 V | 64 mA max (16 mA per chip) | TI SLOS075K, "Total supply current" |
| TL072 (U2) | ±12 V | about 5 mA | *(estimate, ST datasheet to read)* |
| OPA1688 (U6), idle | ±12 V | 3.6 mA max (1.8 mA per amplifier) | TI SBOS724A, section 7.5 |
| Headphones driven hard (32 Ω, both channels, near the current limit) | ±12 V | about 36 mA average per rail | calculated from 56 mA peak |
| **±12 V total, worst case** | | **about 110 mA per rail** | design value: 150 mA per rail |
| Relay coils (all five relays on) | 5 V | 105 mA | Omron G6K datasheet, 21.1 mA per coil |
| Daisy Seed | 5 V | 300 mA | *(estimate; Electrosmith publishes no figure; measure)* |
| LEDs and logic of the control board, through the 3.3 V regulator | 5 V | 300 mA | *(estimate; fixed when the LED driver is chosen)* |
| **5 V total, worst case** | | **about 0.7 A** | |

Input power, worst case: ±15 V module 2 × 15 V × 0.15 A = 4.5 W at 81 %
efficiency = 5.6 W; 5 V module 3.5 W at about 90 % = 3.9 W; input diodes
about 1 W. **Total about 10.5 W, 0.9 A from a 12 V adapter.** In normal use
(headphones at a sane level, LEDs partly lit) about half of that.

**Adapter to buy: 12 V DC, 2 A or more, regulated (switching) type, barrel
plug 5.5 × 2.1 mm.** Either plug polarity works. 2 A is more than twice the
worst-case draw, so the adapter runs cool and its voltage does not sag. A
15 V adapter also works. A 9 V adapter does **not**: after the input diodes
it leaves less than the 9 V the ±15 V module needs to start.

## 3. Block diagram

```
 DC jack ─ PTC fuse ─ bridge (4 diodes) ─●─ diode ─●─ bulk capacitors ── VIN_DC (about 10.8 V with a 12 V adapter)
            TVS across the input         │         │
                                  "adapter present" │
                                   sense node       ├─ 5 V module ───► +5 V ─┬─► relays
                                         │          │                        ├─► Daisy Seed VIN
                                         ▼          │                        └─► 3.3 V regulator ─► control board LEDs / logic
                                   mute delay       │
                                   circuit          └─ ±15 V module ─┬─► +15 V ─ LC ─ regulator ─► +12 V
                                         │              (isolated)   └─► −15 V ─ LC ─ regulator ─► −12 V
                                      MUTE_SW (to K4, K5)
```

## 4. Input: polarity, fuse, transients

- **Bridge of four Schottky diodes (SS34, Basic).** Whatever the polarity of
  the plug, the current finds its way through two of the four diodes. Cost:
  two diode drops (about 0.8 V together) and their heat (about 0.7 W at
  0.9 A). Alternative: an "ideal bridge" controller with four MOSFETs, with
  almost no loss, but an expensive Extended part and four transistors for a
  gain that does not matter here.
- **Resettable fuse (PTC)** in series: it limits the current if something on
  the board shorts, and recovers when the fault is removed.
- **TVS diode** across the input: it clamps voltage spikes (hot-plugging an
  adapter, static) before they reach the converters. Chosen so that it does
  not conduct at 15 V plus adapter tolerance.
- **One more diode between the bridge and the bulk capacitors.** It lets the
  mute circuit see the moment the adapter is unplugged (section 7). Cost:
  another 0.4 V.

## 5. The two converter modules

A module is a small sealed block with the whole converter inside: controller,
inductor or transformer, and capacitors. On our board it needs only the
capacitors its datasheet asks for. The switching, and the layout that makes
switching converters difficult, stay inside the block.

| Rail | Module | Key data | Datasheet | JLCPCB (2026-11-13) |
|---|---|---|---|---|
| ±15 V | **VRA1215YMD-6WR3** (Mornsun design; YLPTEC version stocked) | 9–18 V in, ±15 V, ±200 mA, 6 W, isolated 1500 V, no minimum load, 81–83 % efficiency, accuracy ±1 % typ / ±3 % max, ripple 60 mVpp typ / 85 max, 300 kHz, starts at 9 V or less, input 617 mA at full load from 12 V, maximum 100 µF on each output | Mornsun VRA_YMD-6WR3 (2026.07.31-B/0) | YLPTEC C5369695, Extended, 100 in stock; EVISUN C53454432, 17 |
| +5 V | **K7805-2000R3** (Mornsun design; YLPTEC version stocked) | 8–36 V in, 5 V, 2 A, 92 % efficiency, 400 kHz, pin-compatible with a 7805, needs 22 µF ceramic at input and output, maximum 1000 µF on the output | Mornsun K78xx-2000R3 (2025.09.29-A/9) | YLPTEC C18212380, Extended, 1,310; Mornsun C970791, 539 |

- **Both are through-hole** (a 25.4 × 25.4 mm block and a 3-pin SIP), so they
  are hand-soldered. That is also what makes them easy to buy elsewhere and
  to replace: both follow an industry-standard pin-out that several brands
  make under the same part number.
- **Stock of the ±15 V module is thin (100).** It goes into the design and
  the BOM as a normal part. If JLCPCB/LCSC has none on the day of the order,
  buy the same part number from any distributor and solder it in.
- **The table above is from the Mornsun datasheets**, the original design.
  The YLPTEC datasheets of the parts JLCPCB stocks have now been read
  (section 5.1); where they differ, the YLPTEC figure is the one to design
  with.
- **Headroom.** Worst case ±150 mA from a ±200 mA module (75 %); 0.7 A from a
  2 A module (35 %).
- **The 100 µF limit on each ±15 V output** bounds the capacitors of the LC
  filter and at the regulator inputs. The values are chosen inside it.
- **The module lowers its switching frequency below half load** (datasheet
  note). Whether any of that reaches the audio band is checked on the
  prototype *(measure)*; the LC filter and the regulators are there for it.
- **Why not converters built from parts** (v0.1 of this note: TPS5430,
  MT3608): three switching circuits to lay out correctly, the hardest part of
  a first board, for a few euros saved. They remain the fallback if no module
  can be found at all.

### 5.1 What the YLPTEC datasheets say (read 2026-11-13, files in `docs/datasheet/`)

**VRA1215YMD-6WR3 (C5369695.pdf, "VR(A)B_YMD-6WR3 series", 7 pages)**

| Item | YLPTEC value | Note |
|---|---|---|
| Pins | 1 = −Vin, 2 = +Vin, 3 = +Vo1, 4 = COM, 5 = −Vo2, 6 = not connected | page 6; body 25.4 × 25.4 × 11.0 mm, pins on a 2.54 mm grid. The datasheet adds: if the label on the part differs, the label is right |
| Input | 9–18 V, 30 V maximum surge, starts at 9 V or less | page 1, 3 |
| Output | ±15 V, ±200 mA, no minimum load | page 1 |
| Minimum load when capacitors are fitted | 3 % (6 mA) | page 5, note 2. Our op-amps draw more than that at all times |
| Maximum capacitance on each output | **220 µF** (Mornsun: 100 µF) | page 1; above it the module may not start |
| Accuracy | +15 V: ±1 % typ, ±2 % max. −15 V: ±2 % typ, ±3 % max | page 3 |
| Load regulation, 20–100 %, balanced load | +15 V: ±1 % max. **−15 V: ±4 % typ, ±5 % max** | page 3 |
| Ripple | 50 mVpp typ, 80 max | page 1 |
| Switching frequency | 250 kHz | page 4 |
| Efficiency | 79 % min, 81 % typ | page 1 |
| Input current at 12 V | 640 mA full load, 25 mA no load | page 3 |
| Hot plugging | not supported | page 3 |
| Recommended output filter | 2.2 µH in each output and in the common line, 100 µF before and after, 1 µF ceramic | pages 5–6 |
| Recommended input | 100 µF / 50 V electrolytic, 1 µF ceramic, 10 µH | page 5 |

**K7805-2000R3 (C18212380.pdf, "K78xx-2000R3 series", 5 pages)**

| Item | YLPTEC value | Note |
|---|---|---|
| Pins | 1 = +Vin, 2 = GND, 3 = +Vo | page 5; body 11.6 × 7.5 × 10.2 mm, pins 2.54 mm apart |
| Input | 8–36 V | page 1 |
| Output | 5 V, 2 A, accuracy ±1 % typ, ±3 % max | pages 1–2 |
| Ripple | 45 mVpp typ, 85 max | page 2 |
| Switching frequency | **1.6–2.4 MHz** (Mornsun: 400 kHz) | page 2. It is a different circuit inside the same shape |
| Efficiency | 92 % at minimum input, 89 % at maximum | page 1 |
| Output capacitor | 22 µF / 10 V ceramic; at most 1000 µF in total | pages 1, 4 |
| Reverse polarity, hot plugging | no protection, not supported | pages 3–4 |

**What this changes in the design**

- **The −15 V output is the weak one.** Tolerance and load regulation
  together can take it down to about −13.7 V in the worst case. The −12 V
  regulator needs 1.1 V of headroom (13.1 V), so there is still about 0.6 V
  left, but no more. The +15 V output stays above 14.5 V.
- **"Hot plugging not supported"** on both modules matters, because pushing
  the adapter plug into the jack while the adapter is live is exactly that.
  The TVS diode and an electrolytic bulk capacitor (whose internal resistance
  damps the spike) at the input are therefore required, not optional. Both
  datasheets recommend the same.
- **The bridge already covers "no reverse polarity protection".**
- **Filter capacitors:** at most 220 µF per output of the ±15 V module,
  including what sits at the regulator inputs.
- Two different switching frequencies on the board (250 kHz and about
  2 MHz), both far above the audio band.

## 6. Linear regulators and filtering

Each ±15 V output of the module passes an LC filter (inductor and capacitors), then a
linear regulator. The filter removes most of the switching ripple; the
regulator removes the rest, sets the exact voltage, and isolates the analog
rails from the converters.

| Rail | Part | JLCPCB | Tolerance to confirm |
|---|---|---|---|
| +12 V | 78M12, TO-252 (candidate) | C22458964, Extended, 16,071 | datasheet **to read**: output inside 11.4–12.6 V, dropout |
| −12 V | MC79M12CDTRKG, onsemi, TO-252 | C67852, Extended, 2,538 | −11.4 … −12.6 V over line, load and temperature; dropout 1.1 V (onsemi MC79M00/D) |
| 3.3 V | AMS1117-3.3, SOT-223 | C6186, **Basic**, 1,455,161 | |

- **Why fixed 12 V regulators and not adjustable ones (LM317/LM337).** No
  resistors to set the voltage means nothing that can be mounted wrong and
  put 20 V on the op-amps. The requirement is ±5 %; a fixed regulator is
  specified as a whole. Adjustable parts are in stock too (LM317G C347367,
  LM337S C19267471) if the fixed ones fail the tolerance check.
- **Heat.** Each 12 V regulator drops 3 V: 0.45 W at 150 mA, fine for a
  TO-252 with copper under it. The 3.3 V regulator drops 1.7 V: 0.5 W at
  300 mA.
- **Headroom is the point to watch.** The module gives 15 V −3 % = 14.55 V
  in the worst case, and a little less after the filter. The −12 V regulator
  needs 1.1 V, so it is comfortable. A 78M12 needs about 2 V (figure listed
  by JLCPCB; datasheet to read), which leaves only about 0.5 V of margin. If
  the datasheet confirms that, the +12 V regulator becomes a low-dropout
  type instead. Decided at schematic time, with the datasheet.
- **The onsemi MC79M12CDTRKG is marked "discontinued"** in the revision
  history of its datasheet (27 February 2026). JLCPCB still has 2,538. A
  second source is chosen at schematic time (other makers' 79M12, or the
  adjustable LM337S, C19267471, 1,321 in stock).
- **Acceptance test** (already in the input note, section 11.1): the first
  thing measured on the first board is that each rail is inside
  11.4–12.6 V, before the Seed is fitted.

## 7. Mute at power-up and power-down

`MUTE_SW` must be pulled to ground to switch the output relays on (section 7
of the output note). The circuit that does it has two jobs:

- **At power-up: wait.** Pull `MUTE_SW` low only about 1–2 s after the
  supply is present, when the rails have settled and the Seed's DAC has
  started.
- **At power-down: be first.** Release the relays before the ±12 V rails
  start to fall. The relays need up to 3 ms to open (Omron datasheet), so
  the circuit must notice the loss of the adapter earlier than that.

**How.** The "adapter present" node sits between the bridge and the extra
diode. It has only a small capacitor, so it collapses within a millisecond
when the plug is pulled, while the bulk capacitors behind the diode keep the
converters running for several milliseconds more. A small comparator circuit
watches that node: node high for 1–2 s → relays on; node low → relays off at
once. The coil diode of the mute relays gets a Zener in series so the relays
release fast.

No Daisy pin, no firmware. Exact parts and values are worked out at
schematic time and shown to you before they are drawn. Hold-up time of the
rails against the release time of the relays *(measure)*.

## 8. Grounding

- Two ground nets in the schematic: **GNDA** (analog) and **GND** (digital,
  relays, converters).
- They are joined **at one point, at the Daisy Seed** (its AGND pin 20 and
  DGND). The Seed datasheet requires AGND and DGND to be connected (Fig.
  1.1).
- The converters return their current to the input capacitors, not through
  the analog ground. The headphone return current (tens of mA) goes straight
  back to the ±12 V regulator capacitors, not past the input stages.
- These are layout rules; they are written here so the PCB follows them.

## 9. Decisions

Approved by Antonios on 2026-11-13:

1. **Converter modules** (section 5) instead of converters built from parts.
2. **Adapter: 12 V, 2 A or more, regulated.** The 9–15 V range is dropped;
   15 V still works, 9 V does not.
3. Polarity protection by a diode bridge stays, so any 12 V adapter with a
   5.5 × 2.1 mm plug can be used whatever its polarity.

Mine, explained above, open to objection:

4. Mute circuit as in section 7, analog, watching the adapter node.
5. 3.3 V for the control board from a linear regulator off the 5 V rail,
   allowance 300 mA, revisited when the LED driver is chosen (94 LEDs).
6. Daisy Seed fed with 5 V on VIN.

## 10. Parts still to select (at schematic time, each checked at JLCPCB)

DC jack (through-hole, panel part), PTC fuse, TVS diode, the extra series
diode, inductors and capacitors of the two LC filters (inside the module's
100 µF limit), bulk capacitors, the +12 V regulator and a second source for
the −12 V one, the comparator of the mute circuit.

## 11. To be read before the schematic

- *(done)* YLPTEC datasheets of both modules, section 5.1. Still to do
  with them: check the EasyEDA footprints against the drawings.
- 78M12 datasheet (or the low-dropout alternative): tolerance over load and
  temperature, dropout, minimum capacitors.
- TL072 supply current (ST datasheet).

## 12. To be measured

| What | How | Decides |
|---|---|---|
| ±12 V rails, loaded and unloaded | multimeter | pass: 11.4–12.6 V (before the Seed is fitted) |
| Ripple on ±12 V, +5 V | scope, 20 MHz limit and full bandwidth | filter values |
| Current of the Daisy Seed and of the control board | multimeter in series | budget, adapter rating |
| Temperature of the regulators and converters at full load | thermometer | copper area |
| Power-up and power-down thump at the jacks | scope, single-shot | mute delay and release |
| Switching noise in the audio band | output noise spectrum, effects on | layout, filtering |

## Sources

- Daisy Seed datasheet v1.0.5 (Electrosmith): Table 1 (VIN range), Fig. 1.1 (AGND to DGND).
- NE5532 datasheet, TI SLOS075K: total supply current.
- OPA1688 datasheet, TI SBOS724A: quiescent current.
- Omron G6K datasheet: coil current, release time.
- Mornsun datasheets VRA_YMD-6WR3 & VRB_YMD-6WR3 (2026.07.31-B/0) and K78xx-2000R3 (2025.09.29-A/9).
- onsemi MC79M00/D: MC79M12 output voltage, dropout, revision history.
- JLCPCB part pages of the LCSC numbers above, read on 2026-11-13.
