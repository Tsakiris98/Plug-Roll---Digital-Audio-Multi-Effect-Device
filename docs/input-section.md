# Input Section — Design Note (v0.3, 2026-11-12)

Status: **architecture approved, no schematic yet.** Every number marked
*(measure)* is provisional until it is measured on the real Daisy Seed Rev 5.

Approved on 2026-11-12: output pad 5.6 kΩ / 1 kΩ; INST/LINE relays driven by
the Daisy; analog pots on the control board with shielded analog cables; mono
normalling at the Right receiver input with the Neutrik NMJ6HCD2 jack.

Changes from v0.2: relays are driven by the Daisy, the toggle goes only to a
GPIO, power-on default state added (section 6); jack contacts confirmed on the
Neutrik drawing (section 8); first-board acceptance measurements added
(section 11).

## 1. What the Daisy Seed Rev 5 gives us

| Item | Value | Source |
|---|---|---|
| Codec | WM8731 | Daisy Seed datasheet v1.0.5, schematic 4 of 4 |
| Circuit between the audio input pin and the codec | 0 Ω series, 2.2 µF coupling capacitor, nothing else (shunt capacitor not fitted) | same schematic (R24/C33, R26/C34) |
| ADC full scale | 1.0 Vrms × AVDD/3.3 (1.41 V peak at 3.3 V) | WM8731 datasheet, "Line Input to ADC" |
| Seed datasheet statement | "AC coupled and 3.6 Vpp, or approx. 1 Vrms" | Daisy Seed datasheet v1.0.5, p. 5 |
| Absolute maximum at the Seed audio input pins | −1.8 V … +1.8 V | Daisy Seed datasheet v1.0.5, Table 1 |
| Codec pin absolute maximum | AGND − 0.3 V … AVDD + 0.3 V | WM8731 datasheet, absolute maximum ratings |
| Codec input bias point | VMID = AVDD/2 = 1.65 V | WM8731 datasheet |
| Input resistance | 20 kΩ min, 30 kΩ typ (0 dB gain) | WM8731 datasheet |
| ADC SNR | 85 dB min, 90 dB typ, A-weighted, 48 kHz | WM8731 datasheet |

What this means:

- **The Seed adds no protection of its own.** The pin goes through 0 Ω and a
  capacitor straight to the codec. Whatever limits the voltage and the current
  must be on our board.
- **Where ±1.8 V comes from.** The codec pin rests at 1.65 V. ±1.8 V around
  that is −0.15 V … +3.45 V, just inside the codec's own limit of −0.3 V …
  +3.6 V. The codec limit itself corresponds to ±1.95 V at the Seed pin.
- **The Seed datasheet contradicts itself.** 3.6 Vpp is 1.27 Vrms, not 1 Vrms.
  The codec datasheet says 1.0 Vrms, and "3.6 Vpp" looks like the ±1.8 V
  limit, not the full scale. This note assumes **0 dBFS = 1.0 Vrms = +2.2 dBu
  = 1.41 V peak** at the pin *(measure)*.
- **The limit is only 2.1 dB above full scale** (1.8 V against 1.41 V).

## 2. Block diagram

```
                      K1 (relay)
 L jack tip ─ RF ─────┬─ LINE ──────► LINE receiver L (balanced, −5.8 dB) ──┐
 L jack ring ─ RF ────│─────────────►                                       ├─ K2a ─► L chain
                      └─ INST ──────► INST buffer (1 MΩ, +12 dB) ───┬───────┘
                                      + diode clamp                 │
                                                                    │
 R jack tip ─ RF ───────────────────► LINE receiver R (balanced, −5.8 dB) ──┐
 R jack ring ─ RF ──────────────────►                               │       ├─ K2b ─► R chain
   (R jack empty: its switch contacts connect the R receiver        └───────┘
    inputs to the L receiver inputs)

 L chain / R chain (identical):

   ─► shielded cable ─► GAIN pot on the control board (one gang) ─► shielded cable ─►
      fixed gain +21.6 dB ──●── output pad −16.6 dB ── RC ──► Daisy ADC
                            │
                       "hot node" ──► bypass tap (to the output section)
```

- K1, K2a, K2b are relay contacts, switched together by the Daisy (section 6).
  In INST, both chains take the INST buffer.
- "Hot node" = output of the last op-amp. 0 dBFS at the ADC corresponds to
  +18.9 dBu (9.6 V peak) there.

## 3. Output pad: keep the signal big, attenuate at the very end

**What it does.** The analog chain works at a high level (several volts). A
resistor divider ("pad") directly in front of the Daisy pin brings it down to
codec level. Values: **5.6 kΩ in series, 1 kΩ to ground**, with 2.2 nF C0G
across the 1 kΩ (low-pass at about 88 kHz against RF and out-of-band noise).

**Why.**
1. *Voltage limit by construction.* The op-amp output cannot go beyond its
   supply rails, so the pin cannot go beyond rail × divider ratio.
2. *Current limit by construction.* All current into the Seed passes through
   the 5.6 kΩ.
3. *Noise.* Op-amp noise is attenuated together with the signal.
4. *Bypass and output levels match.* 0 dBFS at the hot node is +18.9 dBu. The
   requirements ask for about +18 dBu maximum output. The output stage needs
   about +16.6 dB after the DAC anyway, and then the bypass signal taken at
   the hot node has the same level as the DAC path.

**Alternative and its cost.** Run the chain at codec level and clamp the pin
with Schottky diodes. Costs: diodes that protect at 1.8 V already conduct
below 1.41 V (distortion on peaks); BAT54S is an Extended part; the bypass
needs about 16 dB make-up gain; op-amp noise is not attenuated.

### 3.1 Check against the datasheets (your question)

What the NE5532 datasheet says about maximum output:

- The current TI datasheet (SLOS075K, December 2025) gives **no output swing
  figure at all**. Its revision history says the row "Maximum peak-to-peak
  output voltage swing" was removed.
- The previous revision (SLOS075J, 2015) gave 24 V min, 26 V typ peak-to-peak
  on ±15 V with a load of 600 Ω or more: the output stops 2 V (typical) to 3 V
  (worst case) short of each rail. That is a guarantee of how far the output
  *reaches*, not of where it *stops*.
- So the only upper limit a datasheet can prove is the supply rail itself.
  Recommended supply is ±5 V to ±15 V, so ±12 V is inside the specified range.

Divider ratio: unloaded 1/6.6 = 0.1515; with the codec's 30 kΩ typ 0.1473
(−16.6 dB); with its 20 kΩ min 0.1453. I assume the ±12 V rails stay within
±5 % (11.4 … 12.6 V). This becomes a requirement for the power supply.

| Op-amp output at | Hot node | Pin, Seed fitted (30 kΩ) | Pin, worst case (unloaded ratio) |
|---|---|---|---|
| Full scale, 0 dBFS | 9.6 V | 1.41 V | |
| Typical swing, nominal rail (12 V − 2 V) | 10.0 V | 1.47 V | 1.52 V |
| Typical swing, rail +5 % (12.6 V − 2 V) | 10.6 V | 1.56 V | 1.61 V |
| 1 V below a +5 % rail (more than the part can do) | 11.6 V | 1.71 V | 1.76 V |
| **Exactly on a +5 % rail (physically impossible)** | 12.6 V | **1.86 V** | **1.91 V** |

**Answer.** In every condition the op-amp can really reach, the pin stays at
or below 1.76 V, inside ±1.8 V. A proof that needs nothing but the datasheet
has to assume the output sits exactly on the rail, and then the pin could be
0.06 to 0.11 V over the Seed limit, still below the codec's own limit
(1.95 V). The real swing and the real pin voltage are measured on the first
board **before the Seed is plugged in** (section 11).

**Current limit.** Seen from the Seed pin, the pad is a voltage source of at
most 1.91 V behind 850 Ω (5.6 kΩ in parallel with 1 kΩ).

| Situation | Current into the Seed pin |
|---|---|
| Normal, full scale | 47 µA peak (1.41 V into 30 kΩ) |
| Pin tries to go over 1.8 V and the codec clamps it there | at most (1.91 − 1.8) V / 850 Ω = **0.13 mA** |
| Any fault at all (pin shorted, Seed unpowered while ±12 V is on) | at most 12.6 V / 5.6 kΩ = **2.3 mA** |

The WM8731 datasheet gives no rating for current forced into an input, so I
cannot quote a guaranteed safe value. Fractions of a milliamp through 5.6 kΩ
are far below what normally harms a CMOS input, and the 2.2 µF capacitor on
the Seed blocks any DC.

**The trade-off in the pad value.**

| Series resistor | Pin if the output were on a +5 % rail | Op-amp level needed for 0 dBFS | Consequence |
|---|---|---|---|
| 5.1 kΩ | 2.01 – 2.07 V | 8.9 V peak | ADC always reaches full scale; larger theoretical excess |
| **5.6 kΩ (chosen)** | 1.86 – 1.91 V | 9.6 V peak | full scale with a typical op-amp; a weak one clips about 0.5 dB earlier |
| 6.2 kΩ | 1.70 – 1.75 V | 10.5 V peak | provably inside ±1.8 V; the op-amp clips 0.4 – 1.9 dB before the ADC, so the last LEDs of the meter would never light |

**Approved: 5.6 kΩ / 1 kΩ.** It is one resistor per channel, so it can still
change to 5.1 kΩ or 6.2 kΩ if the measurements on the first board ask for it.

## 4. Gain staging

Reference: 0 dBFS = +2.2 dBu at the pin = +18.9 dBu at the hot node.
Target −18 dBFS = +0.9 dBu at the hot node.

| Stage | Gain | Resistors (provisional) |
|---|---|---|
| LINE receiver | −5.8 dB (×0.51) | 10 kΩ / 5.1 kΩ differential amplifier |
| INST buffer | +12 dB (×4) | non-inverting, 3 kΩ / 1 kΩ, 1 MΩ to ground at the input |
| GAIN pot | −∞ … 0 dB | 10 kΩ dual-gang audio taper, used as a divider |
| Fixed gain | +21.6 dB (×12) | non-inverting, 11 kΩ / 1 kΩ |
| Output pad | −16.6 dB | 5.6 kΩ / 1 kΩ (with the 30 kΩ of the codec) |

Total range, input jack to hot node: LINE −∞ … +15.7 dB, INST −∞ … +33.6 dB.

| Source | Input level | Total gain needed | Pot setting | ADC level | Notes |
|---|---|---|---|---|---|
| LINE, studio nominal | +4 dBu | −3.1 dB | −18.9 dB | −18 dBFS | around mid rotation of an audio-taper pot |
| LINE, hot peaks | +20 dBu | same | same | −2 dBFS | 2 dB spare without touching the knob |
| LINE, consumer | −10 dBV (−7.8 dBu) | +8.7 dB | −7.1 dB | −18 dBFS | |
| LINE, max before the receiver clips | about +24 dBu | | | | assumes ±9 V swing *(measure)* |
| INST, average guitar *(typical, measure)* | about −18 dBu | +18.9 dB | −14.8 dB | −18 dBFS | |
| INST, weak single coil *(typical)* | about −30 dBu | +30.9 dB | −2.8 dB | −18 dBFS | |
| INST, max before the buffer clips | about 2.3 V peak (+6 dBu) | | | | hot active pickups may exceed this |

Decisions:

- **LINE receiver attenuates by 6 dB.** A +20 dBu signal is 11 V peak, more
  than an op-amp on ±12 V can pass at unity gain. The receiver's resistors
  halve it before the op-amp sees it. Cost: 6 dB of gain made up later, which
  is harmless here (section 5).
- **Gain pot as a passive divider, followed by a fixed gain stage.** Simple,
  can always be turned down to silence, and almost no DC flows through the
  wiper. Alternative: pot in the feedback loop of an op-amp. Less noise at low
  gain, but it cannot go below unity, has an awkward control law, and a remote
  pot inside a feedback loop is asking for instability.
- **INST buffer has +12 dB.** A guitar is 15–20 dB quieter than line level.
  Gain in the first stage puts both modes in the same range of the knob. Cost:
  inputs above about 2.3 V peak clip in the buffer. Synths and keyboards on TS
  cables belong in LINE mode. If your guitars are hotter, this becomes +6 dB
  (one resistor).
- **The two gangs of an audio-taper pot do not track perfectly** (a few dB
  left/right error at low settings is normal for the part).

## 5. Noise estimate (20 Hz – 20 kHz, unweighted, calculated)

Op-amp data: NE5532 5 nV/√Hz and 0.7 pA/√Hz at 1 kHz (TI SLOS075K); TL072
15 nV/√Hz (value listed by JLCPCB for the ST part). Resistor thermal noise at
25 °C.

| Case | Noise at the hot node | Relative to full scale |
|---|---|---|
| LINE, pot at nominal (+4 dBu → −18 dBFS) | 16 µV (−93.7 dBu) | **−113 dBFS** |
| LINE, pot at maximum | 33 µV (−87.4 dBu) | **−106 dBFS** |
| INST, pot at "average guitar", input shorted | 25 µV (−89.8 dBu) | **−109 dBFS** |
| INST, pot at maximum (+33.6 dB), input shorted | 109 µV (−77.1 dBu) | **−96 dBFS** |
| Output pad resistors alone | 0.5 µV at the pin | −126 dBFS |
| **WM8731 ADC (datasheet, A-weighted)** | | **−90 dBFS typ, −85 dBFS min** |

Equivalent input noise: LINE receiver about −104 dBu, INST buffer about
−111 dBu (input shorted; a real pickup adds thermal noise of the same order).

**Conclusion.** In every setting the analog chain is 6 to 23 dB quieter than
the codec's typical figure. The noise floor of this device is the WM8731. The
only way to use it well is level: nominal −18 dBFS leaves about 70 dB between
the signal and the codec floor. A more expensive op-amp would change nothing
audible. Not included in the calculation: hum picked up by the pot cable
(section 7) and the real Rev 5 floor, which forum reports say is worse than
the datasheet. Both are measured.

## 6. INST/LINE switching (relays driven by the Daisy)

**Contacts.** Three changeover contacts, switched together:

- K1: L jack tip goes to the LINE receiver (LINE) or to the INST buffer
  (INST). Without it, the 15 kΩ of the receiver would load the guitar and the
  1 MΩ input would be lost.
- K2a: the L chain takes the L receiver (LINE) or the INST buffer (INST).
- K2b: the R chain takes the R receiver (LINE) or the INST buffer (INST).
  **In INST the right channel always gets the left signal, whatever is plugged
  into the Right jack.**

Two small 2-pole signal relays cover this, with one contact spare. Same relay
type as the bypass relay, so one part number.

**Control.**

- The panel toggle goes **only to a Daisy GPIO** (switch to ground, pull-up to
  3.3 V). It carries a logic level, nothing else, so it can travel in the
  digital ribbon.
- One Daisy GPIO drives both relay coils through a transistor, with a diode
  across the coils to absorb the switch-off spike. Same driver circuit as the
  bypass relay.
- Coil current comes from the logic supply and returns through the digital
  ground, not from the ±12 V analog rails. The hold current in INST mode goes
  into the power budget (value from the relay datasheet, at the schematic).

**Switching sequence (firmware).** When the toggle changes:

1. debounce the toggle (about 20 ms);
2. mute the outputs with the same hardware mute that is used around the bypass
   relay, so both the DSP path and the analog bypass path are silent; fade the
   DSP input to zero, so the switching transient is not recorded into the
   delay and reverb;
3. switch the relays;
4. wait for the contacts to settle (about 10 ms *(measure)*);
5. fade the DSP input back in and release the mute.

**Power-on default (before the firmware runs).**

- A pull-down resistor at the transistor input keeps it off whenever the GPIO
  is not actively driven high: during reset, in the bootloader, with a stopped
  firmware, or with the Seed removed. So the relays are **released** until the
  firmware decides otherwise. This does not depend on what the Daisy pin does
  on its own at reset.
- **Released = LINE.** LINE is the safe state for any source: it accepts up to
  about +24 dBu, while a line signal into the INST buffer would clip it. LINE
  also needs no coil current.
- The outputs are muted during power-up anyway (requirement of the output
  section), so this default state is never heard. At start the firmware reads
  the toggle, sets the relays while still muted, waits for them to settle, and
  only then releases the mute. Powering up with the toggle on INST therefore
  gives no click.
- At power-down the relays fall back to LINE while the outputs are muted.

**Trade-offs.**

- Against the toggle driving the coils directly: no click, at the cost of one
  more GPIO and a transistor. If the firmware stops, the mode can no longer be
  changed; acceptable, because the device processes nothing without firmware.
- Against latching relays (they keep their state without coil current): they
  need two drive signals per relay and their state is unknown at start, so the
  firmware would have to set them anyway. Not worth the extra parts.

GPIOs used by the input section: toggle (in), relays (out), Right jack
detection (in). LCSC part for the relay and transistor: at the schematic.

## 7. Analog pots on the control board (decided)

All pots stay on the control board. The pre-amp gain pot gets a **dedicated
short shielded analog connection**, separate from the digital ribbon. The same
rule applies to master volume and HP volume (output section).

What matters for the gain pot, and why:

- **Its ground is the main board's analog ground, brought over in the same
  cable.** The bottom end of the pot is the reference of the following ×12
  stage. If it were tied to the control board's ground, every millivolt of LED
  and scanning current noise between the two boards would be amplified 12
  times. The pot must not touch the control board ground at all.
- **Input and output pots do not share a cable.** The wiper of the gain pot
  is a sensitive point followed by ×12. If it ran next to the master volume
  wires (the output of the same device), the output would leak back into the
  input: a feedback path around the whole effect chain. So: one shielded cable
  for the gain pot, a separate one for master + HP volume, connectors apart.
- **Each wiper wire is shielded**, shield connected at the main board only.
  The wiper is the only point in the chain with a few kΩ of impedance
  (2.5 kΩ at worst); everything else is driven by op-amp outputs.
- **A 100 kΩ resistor from the wiper input to ground on the main board**, so
  the stage stays quiet if the cable is unplugged.
- Conductors for the gain pot: L top, L wiper, R top, R wiper, analog ground,
  shield. Connector and cable type (with LCSC number): at the schematic.

Cost of this decision against a pot on the main board: one more cable and two
connectors, and some risk of hum pickup that only the prototype can quantify.

## 8. Mono normalling and jack (approved)

**Jack.** Neutrik NMJ6HCD2, 6.35 mm TRS, horizontal PCB mount, through-hole.
LCSC **C368502**, 772 in stock on 2026-11-12. Used for both inputs
(hand-soldered).

**Two separate jacks, one per channel: Left and Right.** Neutrik calls the
part "stereo" only because it has three conductors. Here each jack carries
one balanced mono channel: tip = hot (+), ring = cold (−), sleeve = ground.
A TS plug also works (the ring is then grounded by the plug).

**Contact arrangement, confirmed from Neutrik.**

- Drawing ST-NMJ6HCD2 (released 26.02.2021): six PCB pins in two rows
  16.23 mm apart. One row is **T, R, S**, the other **TN, RN, SN**, at 16.7,
  10.35 and 4 mm from the panel face. Hole diameter 1.4 mm, panel cut-out
  11.4 mm.
- Neutrik "Jacks – Circuits" list: type N\*J6\*\* is "3x switching
  (normalling) Stereo". Each of TN, RN, SN rests on its own T, R, S spring
  while the jack is empty and opens when a plug is inserted.
- Switch contact rating: 0.5 A at 50 V (Neutrik product page). Far above what
  a line signal or a logic input needs.

These are *normalling* contacts, not an isolated switch: a contact can only
feed something into the jack's own terminals, that is, into the input of the
Right receiver. That is why the normalling is done at the receiver input.

**Implementation.**

- R jack **TN** → L receiver hot input (taken after K1); R jack **RN** → L
  receiver cold input. With the Right jack empty, both receivers listen to the
  Left jack. The right channel then carries the left signal for the DSP and
  for the analog bypass, at the same level.
- R jack **SN** → Daisy GPIO with pull-up: low while the jack is empty, high
  when a plug is in. This is the mono detection.
- L jack TN and RN → ground, so an empty Left input is silent. L jack SN is
  not used.
- No relay, no extra parts. The source sees two receivers in parallel (about
  10 kΩ balanced), which any line output drives without effort.
- In INST the normalling does not matter: K2b gives the right chain the INST
  buffer. Because the R jack's TN is wired after K1, the Right receiver does
  not load the guitar either.

## 9. Input protection

- **LINE inputs.** The receiver's own 10 kΩ input resistors limit the current.
  A BAV99 at each op-amp input steers anything beyond the ±12 V rails into the
  supply. DC-blocking capacitors in front (about 10 µF, rated 50 V or more,
  1.6 Hz corner) stop DC from a faulty source. 100 pF C0G from each leg to
  ground at the jack shorts radio frequencies.
- **INST input.** 1 kΩ series resistor, 100 pF to ground, BAV99 to the rails,
  100 nF blocking capacitor into 1 MΩ (1.6 Hz corner). The 1 kΩ is a
  compromise: larger protects better but adds hiss (1 kΩ adds 4 nV/√Hz against
  the 15 nV/√Hz of the op-amp).
- **Daisy pin.** Protected by the pad (section 3). No diodes.
- **Receiver precision.** A balanced receiver rejects hum only as well as its
  four resistors match: about 30 dB with 1 % parts, about 50 dB with 0.1 %.
  I recommend 0.1 % for these eight resistors even if they are Extended. To be
  checked at JLCPCB.

## 10. Parts

Checked on jlcpcb.com / lcsc.com on 2026-11-12.

| Function | Part | LCSC | Library | Stock | Why |
|---|---|---|---|---|---|
| Main op-amp (receivers, gain stages) | NE5532DR, TI, SOIC-8, dual | C7426 | **Basic** | 266,045 | low noise, drives low impedances, ±15 V rated |
| INST buffer | TL072CDT, ST, SO-8, dual | C6961 | **Basic** | 124,003 | FET input: practically no input current |
| Input clamp diodes | BAV99,215, Nexperia, SOT-23 | C2500 | **Basic** | 1,923,653 | steers overvoltage to the supply rails |
| Input jacks L and R | NMJ6HCD2, Neutrik, THT | C368502 | hand-soldered | 772 (LCSC) | TRS with 3 normalling contacts, see section 8 |
| Rejected: Schottky pair | BAT54S,215, Nexperia | C47546 | Extended | 264,880 | not needed with the pad |

**Why two op-amp types.** The NE5532 has bipolar inputs that draw 200 nA typ,
800 nA max (TI SLOS075K). Through the 1 MΩ a guitar input needs, that is 0.2
to 0.8 V of DC offset, and its current noise through a high-impedance pickup
would hiss. The TL072 draws picoamps, so it is the right part for the one
high-impedance node. Everywhere else impedances are low and the NE5532 is
about 10 dB quieter. Both are Basic, so the second type costs no fee.
Alternative: one FET-input audio op-amp everywhere (OPA1678 class). It is
Extended and I could not confirm its stock, and section 5 shows it would not
be audible.

Count: 2× NE5532 (L/R receivers, L/R gain stages) + 1× TL072 (INST buffer, one
half spare and tied off).

**Not selected yet** (chosen with LCSC check when the schematic starts):
resistors and capacitors (0603, Basic where possible; 0.1 % for the
receivers), DC-blocking capacitors, relays and their driver transistor, gain
pot, pot cable and connectors, INST/LINE toggle, alternative parts for the two
op-amps.

## 11. To be measured

### 11.1 First-board acceptance test (required, before the Seed is plugged in)

Done on the assembled main board with the Daisy Seed **not fitted**. Without
the Seed the pad is unloaded, which is the highest voltage the pin can ever
see, so the test is safe and worst-case at the same time.

| Step | Measurement | Pass condition |
|---|---|---|
| 1 | +12 V and −12 V rails with a multimeter | each within 11.4 … 12.6 V |
| 2 | Drive each channel hard into clipping (1 kHz sine, gain at maximum). Oscilloscope on the hot node: positive and negative peak | record both values: this is the real swing of the NE5532 |
| 3 | Same signal, oscilloscope on the Daisy audio input pin of the socket: positive and negative peak | **both inside ±1.8 V** |
| 4 | Switch power on and off several times with the scope on the same pin (single-shot trigger) | no excursion beyond ±1.8 V |

Then fit the Seed and repeat step 3 once. The loaded value must be lower than
the unloaded one. If step 3 or 4 fails, the series resistor goes to 6.2 kΩ
before the Seed is ever fitted. The measured values are written into this
note.

### 11.2 Other measurements

| What | How | Decides |
|---|---|---|
| ADC full scale of this Rev 5 Seed | sine of known Vrms into the pin, read dBFS in firmware | pad ratio |
| Input resistance of the Seed pin | level drop through a known series resistor | pad ratio |
| ADC noise floor | input shorted through 850 Ω, read RMS in firmware | real dynamic range |
| DAC full scale and noise | firmware sine out, measure Vrms | output section gain |
| Hum and noise with the pot cable fitted | input shorted, gain at maximum | cable routing and shielding |
| Relay settle time, residual click when switching INST/LINE | scope and listening | wait time in the switching sequence |
| Level of your instruments | guitar/synth into a scope or interface | INST buffer gain (+12 or +6 dB) |

## Sources

- Daisy Seed datasheet v1.0.5 (Electrosmith): Table 1, p. 5; Fig. 1.2; schematic 4 of 4.
- WM8731 / WM8731L datasheet (Wolfson, Production Data rev 3.4): absolute maximum ratings, "Line Input to ADC", Figure 11.
- NE5532 datasheet, TI SLOS075K (December 2025): sections 5.1, 5.3, 5.5, 5.6 and revision history. Output swing figures of SLOS075J (2015) as quoted by TI's document viewer.
- Electrosmith forum: "Rev5 seed producing ~13dB higher noise floor".
- Neutrik: drawing ST-NMJ6HCD2, "Jacks – Circuits" list (2015/09/15), product page NMJ6HCD2.
- JLCPCB part pages C7426, C6961, C2500, C47546; LCSC product page C368502.
