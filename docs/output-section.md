# Output Section — Design Note (v0.1, 2026-11-12)

Status: **approved on 2026-11-12 (all items of section 9); requirements
updated to v0.6.** The whole output section is in the schematic (sheets `output-dac`,
`output-pots`, `output-jacks`). The circuit that switches the mute relays
(`MUTE_SW`) is designed with the power supply. Every number marked *(measure)* is
provisional until it is measured on the real board.

Covers: DAC gain stage, global bypass relay, master volume and line outputs,
headphone amplifier, power-up/power-down mute.

## 1. What the Daisy Seed Rev 5 gives us at the output

| Item | Value | Source |
|---|---|---|
| Pins | 18 = Audio Out L, 19 = Audio Out R, 20 = AGND | Daisy Seed datasheet v1.0.5, pin table |
| Circuit between the codec and the pin | 2.2 µF series capacitor, 47 kΩ to AGND, 100 Ω in series | Daisy Seed datasheet v1.0.5, schematic 4 of 4 (C64/R29/R30, C65/R28/R31) |
| DAC full scale | 1.0 Vrms × AVDD/3.3 (1.41 V peak) | WM8731 datasheet, "Line Output for DAC Playback Only" |
| Seed statement | "0dBFs @ 1Vrms", output impedance 100 Ω | Daisy Seed datasheet v1.0.5, Table 2 and Fig. 1.7 |
| Load the DAC figures are specified for | 10 kΩ, 50 pF | WM8731 datasheet |
| DAC SNR | 95 dB min, 100 dB typ, A-weighted, 48 kHz | WM8731 datasheet |

What this means:

- **The pin gives a plain AC audio signal around 0 V.** The coupling capacitor
  is on the Seed. Our board adds no bias. It must load the pin with 10 kΩ or
  more: with the Seed's 2.2 µF, a 100 kΩ load gives a low corner of 0.7 Hz.
- **1.0 Vrms is +2.2 dBu.** The requirement is about +18 dBu at the line
  outputs, so the DAC signal needs gain. The Seed cannot drive headphones or
  a balanced line by itself.
- **The DAC is quieter than the ADC** (100 dB against 90 dB typ), so the ADC
  stays the noise floor of the device.

## 2. Block diagram

```
 Daisy pin 18/19 ─► DAC gain ×6.6 (+16.4 dB) ─► C ─┐
                                                   ├─ K3 (bypass relay) ─●─► master pot ─► line buffer ─► K4 (mute) ─► balanced line out L/R
 HOT_L / HOT_R (from the input section) ─────► C ──┘                     │
                                                                         └─► HP pot ─► headphone amp ─► K5 (mute) ─► headphones
```

- Everything is drawn once; left and right are identical.
- "C" = coupling capacitor with a resistor to ground on the relay side
  (section 4).
- Both pots are on the control board (section 6).
- K3 is driven by the Daisy (bypass is a panel button with LED). K4 and K5
  are driven by a small analog power-on delay circuit, not by the Daisy
  (section 7).

## 3. DAC gain stage

**What it does.** A non-inverting amplifier brings the DAC signal up to the
level of the hot node, so that the DSP path and the analog bypass path arrive
at the bypass relay with the same level.

**Values.** Gain 1 + 5.6 kΩ / 1 kΩ = ×6.6 (+16.4 dB): the same two resistor
values as the ADC pad, used the other way round. 100 kΩ from the input to
ground (load for the Seed's capacitor), 100 pF across the 5.6 kΩ (bandwidth
about 280 kHz, keeps radio frequencies out). Op-amp: NE5532 (one chip for
both channels).

**Levels.**

| Point | 0 dBFS | Nominal (−18 dBFS) |
|---|---|---|
| Daisy output pin | 1.0 Vrms, +2.2 dBu | −15.8 dBu |
| After the gain stage | 6.6 Vrms, 9.3 V peak, +18.6 dBu | +0.6 dBu |
| Hot node (bypass path, from the input note) | +18.9 dBu | +0.9 dBu |

- **A/B level match.** Through the whole DSP path (pad, ADC, DAC, gain) the
  signal comes back 0.25 dB lower than the bypass signal, because the codec's
  30 kΩ input loads the pad a little. This is smaller than the tolerance of
  the codec itself. It is measured on the first board and trimmed with one
  resistor or in firmware *(measure)*.
- **Headroom.** 9.3 V peak on ±12 V rails needs the op-amp to reach within
  2.7 V of the rail. Same margin as the input gain stage.
- **Noise.** Gain stage about 6 µV at its output; the DAC's own noise,
  amplified, is about 66 µV. The analog stage is 20 dB below the DAC.

**Alternative and its cost.** Lower output level (for example gain ×4, +14
dBu maximum): more op-amp headroom, but the bypass would then need an
attenuator to match, and the maximum output falls below the requirement.

## 4. Global bypass (relay K3)

**What it does.** One 2-pole relay (the same Omron G6K-2F-Y-5V as the input
relays) selects, for each channel, the DSP path or the hot node of the input
section. It sits before both volume pots, so the master volume and the
headphones follow the bypass state.

**Control.** A Daisy pin drives the coil through a transistor (AO3400A, with
100 Ω at the gate, 100 kΩ pull-down and a 1N4148W across the coil). This is
the one place where the firmware switches an analog path, because the control
is a button with an LED. It costs **one Daisy pin**.

**Released state = bypass.** With no coil current the relay passes the analog
bypass signal. Reasons:

- The main board can be tested completely **without the Seed fitted**: signal
  in, signal out through the bypass path. This fits the first-board acceptance
  test of the input note, which is done before the Seed is plugged in.
- If the firmware stops, audio still passes.
- Cost: the coil draws 21 mA whenever the effects are active.

**No click without a firmware mute.** A click at a relay comes from the two
sources sitting at slightly different DC voltages. Each source therefore goes
through a coupling capacitor (10 µF, the same part as in the LINE receivers)
with 100 kΩ to ground on the relay side. Both relay contacts then rest at
0 V and there is no DC step to switch. What remains is the jump between two
different waveforms, which is the A/B comparison itself. Residual click
*(measure)*.

**Alternative and its cost.** Mute from the firmware around the switch (as the
requirements say now): needs the mute relays to be driven by the Daisy too,
one more pin and more firmware. See section 9.

## 5. Master volume and line outputs

- **Master volume:** 10 kΩ dual-gang audio-taper pot on the control board,
  used as a passive divider directly after the bypass relay.
- **Line buffer:** unity-gain follower after the wiper (NE5532, one chip for
  both channels). It gives the output a low, constant impedance whatever the
  position of the pot. 100 kΩ from the wiper input to ground, so the stage
  stays quiet with the cable unplugged.
- **Impedance-balanced output:** tip = signal through 100 Ω and 10 µF; ring =
  the same 100 Ω and 10 µF to ground, carrying no signal; sleeve = ground. A
  balanced input at the other end still rejects hum picked up on the cable,
  because both wires have the same impedance to ground. With a TS cable the
  ring is simply shorted to ground. Cost against a fully balanced output (a
  second, inverted signal on the ring): 6 dB less level into a balanced
  input, one op-amp less per channel, and no trouble when a TS plug shorts
  the ring.
- **Output capacitors (10 µF, 50 V):** they keep a DC voltage that the
  connected equipment may put on the line away from the op-amp. Into 10 kΩ
  the low corner is 1.6 Hz. 100 kΩ to ground on the jack side.
- **Maximum level:** +18.6 dBu at full volume (requirement: about +18 dBu).
- **Jacks:** Neutrik NMJ6HCD2, the same part as the inputs. The switch
  contacts are not used.

## 6. The two volume pots and their cable

Both pots (master, HP) are on the control board, like the gain pot. They
carry audio, so they stay out of the general ribbon and are referenced to
the main board's analog ground.

The signals here are different from the gain pot: several volts instead of
millivolts, and followed by unity gain instead of ×11. Hum picked up on the
wires is therefore at least 20 dB less critical.

**Proposal: one separate 16-wire ribbon cable (2×8 IDC) for both pots.**
Eight signal wires (top and wiper of four pot sections), each with a ground
wire next to it.

| Option | For | Against |
|---|---|---|
| **16-wire ribbon, ground between signals (proposed)** | one cable, ready-made, no crimping; grounds between the wires keep left/right crosstalk low | not shielded; hum pickup to be checked on the prototype |
| Four shielded 3.5 mm cables (as for the gain pot) | best shielding | four more cables and eight more jacks; six audio cables in total |

Master and HP are both on the output side, so they may share a cable. They
do not share one with the gain pot (output leaking back into the input).

## 7. Mute at power-up and power-down

**Why it is needed.** While the ±12 V rails rise and fall, op-amp outputs
jump by volts, and the Seed's DAC produces its own thump when it starts.
Into headphones or powered speakers that is a loud bang.

**What it does.** Two relays (G6K-2F-Y-5V again) sit in series with the four
outputs (K4: line L/R, K5: headphones L/R), directly before the jacks.
Released = muted: the amplifier is disconnected **and the jack contact is
tied to ground** (changeover contact: moving contact = jack, rest contact =
ground, working contact = amplifier). A grounded output is silent; an output
left open would let the connected equipment hum. So the outputs are muted
whenever the device has no power, and stay muted until the relays are
switched on. The coils sit between +5 V and the line `MUTE_SW`, which the
delay circuit pulls to ground.

**Control: analog, no Daisy pin.** A small circuit switches the relays on
about 1–2 s after the supply is present and switches them off quickly when
the input voltage starts to fall, before the rails collapse. It is designed
together with the power supply, because it watches the input voltage.

**Trade-off.** The firmware cannot mute the outputs. That matches the rule
that analog switching is not done in firmware. If a firmware mute is wanted
later, one transistor and one Daisy pin add it.

Coil current: 42 mA for K4 + K5, always on while the device runs.

## 8. Headphone amplifier

**Requirement.** 32–300 Ω headphones, low output impedance, own volume pot.

**What the two ends of that range need.**

- 300 Ω headphones need *voltage*: several volts.
- 32 Ω headphones need *current*: 1 Vrms is already 31 mA.

A normal audio op-amp (NE5532) has the voltage but not the current for 32 Ω.

**Proposal: TI OPA1688, one dual op-amp for both channels.**

| Property | Value | Source |
|---|---|---|
| Supply | ±2.25 V … ±18 V | TI SBOS724A, section 7.3 |
| Output current (short-circuit) | ±75 mA | SBOS724A, section 7.5 |
| Output swing from the rail | 0.33 V typ at 2 kΩ load (on ±18 V) | SBOS724A, section 7.5 |
| Distortion, 10 mW into 32 Ω, 1 kHz | −109 dB | SBOS724A, section 7.5 |
| Noise | 8 nV/√Hz at 1 kHz | SBOS724A, section 7.5 |
| Input bias current | ±10 pA typ (CMOS input) | SBOS724A, section 7.5 |
| Package and pinout | SOIC-8, standard dual op-amp pinout | SBOS724A, section 6 |
| Thermal resistance, SOIC-8 | 116 °C/W junction to ambient | SBOS724A, section 7.4 |

- **Topology.** HP pot as a passive divider after the bypass relay, then the
  OPA1688 as a follower (gain ×1), then **4.7 Ω in series** (Basic, C23164),
  mute relay, jack.
- **Why 4.7 Ω.** TI states that the OPA1688 needs no series resistor for
  stability (SBOS724A, section 9.2.1.2: about 50° phase margin with 400 pF
  directly at the output). The resistor is there for another reason: a TRS
  plug shorts the contacts of the jack while it is pushed in, and the
  datasheet allows a continuous short circuit only on one amplifier of the
  package at a time (section 7.1, note 3). 4.7 Ω keeps the output impedance
  low (about 5 Ω) and dissipates only 26 mW at the 75 mA current limit.
- **Limits read from the datasheet:** supply ±20 V absolute maximum, junction
  temperature 150 °C maximum (section 7.1). TI's own headphone example on
  ±5 V reaches 50 mW into 32 Ω before clipping (Table 9-1); on our ±12 V the
  current limit is the same, so expect a similar figure into 32 Ω and far
  more voltage into 300 Ω.
- **Why gain ×1 is enough.** The signal at the pot is already hot: nominal
  −18 dBFS is 0.83 Vrms, which is 21 mW into 32 Ω, loud. Full scale is
  6.6 Vrms.
- **The CMOS input draws picoamps**, so the HP pot cannot rustle.
- **Available output (calculated, not guaranteed):** into 300 Ω up to the
  full 6.6 Vrms (145 mW). Into 32 Ω the current limit decides: at most 75 mA
  peak, that is about 1.7 Vrms (90 mW); the clean range ends lower
  *(measure)*.
- **Jack:** one NMJ6HCD2 used as a stereo jack: tip = left, ring = right,
  sleeve = ground.

**Known risk: heat with 32 Ω at full volume.** If a full-scale sine is driven
into 32 Ω with the pot at maximum, the chip sits in current limit and
dissipates up to about 1 W, far too much for an SOIC-8 (116 °C/W). Music has
a much lower average level and nobody listens at that setting, but the board
must survive it. Plan: generous copper under the chip, and a full-scale test
with a 32 Ω load on the prototype *(measure)*. If it runs too hot, the fix is
a resistor value (more series resistance) or the alternative below.

**Alternatives.**

| Part | For | Against |
|---|---|---|
| **OPA1688IDR (proposed)** | simple op-amp circuit, same footprint as every other op-amp on the board | Extended; current limit 75 mA; heat at 32 Ω full scale |
| TPA6120A2DWPR, TI | built as a headphone amplifier, far more current, thermal pad | Extended; 20-pin power package; a current-feedback amplifier, less forgiving in layout and resistor choice |
| NE5532, two halves in parallel per channel | Basic | not specified for 32 Ω; higher distortion; two chips |

### 8.1 Upgrade path: TPA6120A2 (noted on 2026-11-12, not designed)

Antonios wants this kept as the planned upgrade if the OPA1688 runs too hot
or if a higher-grade headphone stage is wanted later.

- **Part:** TI TPA6120A2DWPR, LCSC C70439, Extended, 1,894 in stock at JLCPCB
  on 2026-11-12. JLCPCB lists it as a 2-channel class-AB headphone amplifier
  in a 20-pin HSOP power package with a thermal pad.
- **Why it would solve the heat problem:** the package is built to pass its
  heat into the board copper through the thermal pad, and the part is made
  to deliver headphone currents, so the 32 Ω full-scale case is inside its
  intended use instead of at the current limit of a small op-amp.
- **What it costs:** it is not a drop-in replacement. Different footprint
  (20 pins and a pad that must be soldered to a copper area with vias), a
  current-feedback amplifier whose feedback resistor values are prescribed by
  the datasheet, and a layout that needs more care. It means a new revision
  of the headphone part of the main board.
- **Not yet read from the TI datasheet** (required before any design):
  supply range on our ±12 V rails, output current, thermal resistance with
  the pad soldered, recommended feedback resistors and gain, output series
  resistor, quiescent current for the power budget.
- **How to keep the door open in revision 1:** place the headphone amplifier
  in its own corner of the board, next to the headphone jack, with free
  copper area around it, so that a later revision can swap the block without
  moving anything else.

## 9. Decisions (all approved on 2026-11-12) and changes to the requirements

1. **Gain ×6.6 after the DAC**, maximum output +18.6 dBu. (Requirements say
   "about +16.6 dB" and "about +18 dBu": consistent, values now fixed.)
2. **Bypass relay driven by the Daisy, released = bypass.** One Daisy pin.
   Not stated in the requirements; new.
3. **No mute while the bypass relay switches.** The requirements say "the
   outputs are muted for a few milliseconds while the relay switches". The
   proposal replaces that with coupling capacitors that remove the cause of
   the click. **Conflict with the requirements; needs your decision.**
4. **Power-up/power-down mute done by an analog circuit and two relays,
   without the Daisy.** The requirements ask for the mute but do not say how.
5. **Impedance-balanced line outputs** (already in the requirements), 100 Ω
   per leg, output capacitors.
6. **One 16-wire ribbon for the master and HP pots**, separate from the
   general ribbon and from the gain pot cables. The requirements say "short,
   shielded analog cables": a ribbon with ground wires is not shielded.
   **Departure from the requirements; needs your decision.**
7. **Headphone amplifier OPA1688, gain ×1.** One more Extended part.
8. **Proposed change to the input section:** the same coupling capacitors in
   front of K2 (outputs of the two LINE receivers and of the INST buffer:
   three capacitors, three resistors). It removes the cause of the INST/LINE
   click that the input note lists as an accepted cost, and it takes DC off
   the gain pot. It changes sheets that are already drawn and committed.

Daisy pins used by the output section: **one** (bypass relay).

## 10. Parts

Stock and library status read from jlcpcb.com on 2026-11-12. Parts already in
the JLCPCB library are marked "in library".

| Function | Part | Package | LCSC | Library | JLCPCB stock | Qty |
|---|---|---|---|---|---|---|
| DAC gain, line buffer | NE5532DR, TI | SOIC-8 | C7426 | Basic, in library | 264,815 | 2 |
| Headphone amplifier | OPA1688IDR, TI | SOIC-8 | C206212 | **Extended** | 7,766 | 1 |
| Bypass and mute relays | G6K-2F-Y-5V, Omron | SMD 10 × 6.5 mm | C2982926 | Extended, in library | 29,304 | 3 |
| Relay drivers | AO3400A, AOS | SOT-23 | C20917 | Basic, in library | 1,045,279 | 2 |
| Coil diodes | 1N4148W | SOD-123 | C81598 | Basic, in library | | 2 |
| Output and headphone jacks | NMJ6HCD2, Neutrik (through-hole) | | C368502 | in library | 772 | 3 |
| Resistors 100 Ω, 1 kΩ, 5.6 kΩ, 100 kΩ; capacitors 100 pF, 100 nF, 10 µF | as in the input section | 0603 / 1206 | | Basic, in library | | |
| Headphone output resistor 4.7 Ω 1 % | 0603WAF470KT5E | 0603 | C23164 | Basic | 859,921 | 2 |
| 2×8 IDC box header for the pot ribbon (through-hole) | 321016SG0ABK00A01, JILN | 2.54 mm | C429960 | Extended | 11,151 | 1 |

Alternative for the headphone amplifier: TPA6120A2DWPR, C70439, Extended,
1,894 in stock. OPA1688ID (C544851, tube packaging) is out of stock; the reel
version above is the one to use.

**The pot ribbon header is through-hole, hand-soldered.** The only SMD 2×8
IDC header found at JLCPCB (B-3000N16P-0110, C383608) has 113 pieces in
stock, too few to rely on. A cable header is also pulled and pushed by hand,
and through-hole pins hold much better than SMD pads. Pin use: odd pins =
signals (1 M_TOP_L, 3 M_WIP_L, 5 M_TOP_R, 7 M_WIP_R, 9 HP_TOP_L, 11 HP_WIP_L,
13 HP_TOP_R, 15 HP_WIP_R), even pins = analog ground. In a flat ribbon the
wires follow the pin numbers, so every signal wire lies between two ground
wires.

The power-on delay circuit and its parts are chosen with the power supply.

Coil current on the 5 V rail with everything on: input relays 42 mA (INST),
bypass 21 mA, mute 42 mA = about 105 mA. This goes into the power budget.

## 11. To be measured

| What | How | Decides |
|---|---|---|
| DAC full scale of this Rev 5 Seed | firmware sine at 0 dBFS, Vrms at pin 18/19 | gain of the DAC stage |
| Level difference DSP path against bypass | same input, both relay positions, Vrms at the output | trim resistor or firmware trim |
| Click of the bypass relay | scope at the line output and listening | whether a mute is needed after all |
| Thump at power-up and power-down | scope at the jacks, single-shot | delay and release time of the mute circuit |
| Headphone amplifier: maximum clean level into 32 Ω and 300 Ω, chip temperature with a full-scale sine into 32 Ω | scope, dummy loads, thermometer | series resistor, copper area, or the TPA6120A2 |
| Hum and left/right crosstalk through the pot ribbon | input shorted / one channel driven, volume at mid position | ribbon or shielded cables |
| Output noise at full volume | input shorted, effects on | confirms that the codec is the noise floor |

## Sources

- Daisy Seed datasheet v1.0.5 (Electrosmith): pin table, Table 2, Fig. 1.7, schematic 4 of 4.
- WM8731 / WM8731L datasheet (Wolfson, Production Data rev 3.4): "Line Output for DAC Playback Only".
- OPA1688 datasheet, TI SBOS724A (June 2022): sections 6, 7.3, 7.4, 7.5, 8.3.3, read in TI's document viewer. Read from the PDF as well: sections 7.1, 8.3.3 and 9.2.1 (Table 9-1).
- Omron G6K datasheet (en-g6k.pdf): coil and contact data.
- JLCPCB part pages of the LCSC numbers in section 10.
