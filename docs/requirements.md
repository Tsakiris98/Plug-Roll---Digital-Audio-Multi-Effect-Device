# Plug & Roll — Requirements Specification (v0.6)

> Source of truth for the project. Any change to requirements is made here first.

## Description

This will be a hardware desktop plug-and-play audio multi-effect device, built as a prototype for personal use. It must serve two use cases: an instrument player (guitar, keyboard, synth) plugging an instrument directly into it, and a music producer passing an insert loop of a recording track from an audio interface through it. The device is digital, based on a Daisy Seed audio microcontroller. It accepts both a mono instrument source and a line-level L-R stereo source. It always processes the audio in stereo (Mono/Stereo and Stereo/Stereo) and outputs it at line level.

The effect chain order is fixed and is listed in the Effect Chain section. Every effect section has its own group of potentiometers and buttons on the front panel. Since it is a desktop device, there are no footswitches: only good-quality knobs and buttons, for a professional, high-end look and feel. The device is large on purpose, so that every section is comfortable to use.

Document revision: v0.6. Changes from v0.5 (output section decisions, see `docs/output-section.md`): DAC gain ×6.6; bypass relay released = analog bypass; no firmware mute around the bypass relay (coupling capacitors remove the DC step instead, also in front of the INST/LINE relay); power-up/power-down mute by relays and an analog delay circuit, without the Daisy; master and HP pots on one separate 16-wire ribbon; headphone amplifier OPA1688.

v0.5. Changes from v0.4: **analog switching is not controlled by the Daisy.** The INST/LINE toggle switches the input relay coils directly; no Daisy pin is used for INST/LINE or for mono detection. The global bypass stays a Daisy-driven relay (it is a panel button with LED).

v0.4. Changes from v0.3: SMD parts wherever a part exists in SMD (the signal relays are now SMD); 5 V logic rail required for the relay coils.

v0.3. Changes from v0.2 (input section decisions, see `docs/input-section.md`): INST/LINE switching with relays driven by the Daisy, panel toggle read by a GPIO; analog pots stay on the control board with dedicated shielded analog cables; mono normalling at the Right receiver input with a switched input jack; ADC protected by a resistive pad instead of clamp diodes; bypass tap and output gain defined around the pad; ±12 V rail tolerance added.

v0.2 (revised plan). Changes from v0.1: corrected errors and contradictions, defined the hardware architecture, power, bypass, controls, metering and front panel, and added the missing parameters.

## Scope and Design Rules

### Scope

- Prototype for personal use. No certification (CE/FCC), no battery, no MIDI, no presets.
- Effect emulations are approximations built with classic DSP (detector, ballistics, curves, saturation) that capture the behavior and sound of the original units. No physical modeling.
- All effect parameters are controlled by absolute potentiometers. The only encoder is the delay time encoder.

### Parts and Fabrication Rules

- Fabrication and SMD assembly at JLCPCB. **Every SMD part must have an LCSC part number** (Cxxxxx) stored as a field in its KiCad symbol, and must be in stock at JLCPCB when it is chosen.
- **Basic parts first** (no setup fee). Extended parts only where audio quality depends on them (audio op-amps, headphone driver, DC-DC, LED driver, multiplexers). Keep the number of unique extended parts low, for example one op-amp type used everywhere.
- Passives (R, C) in 0603, so they can be reworked by hand if needed.
- Symbols and footprints come from the LCSC/EasyEDA library (easyeda2kicad), so every footprint matches the exact part that the factory will place. No hand-drawn footprints unless a part has none.
- BOM and CPL are generated with the kicad-jlcpcb-tools plugin. Part rotations are checked in the JLCPCB 3D preview before ordering.
- **SMD wherever a part exists in SMD**, so that JLCPCB places it. Through-hole is used only for panel and mechanical parts (pots, 6.35 mm jacks, buttons, encoder, DC jack, Daisy Seed headers) or when no SMD version is in stock. These are ordered from LCSC together with the PCB order and are **hand-soldered**. Relays are SMD signal relays.
- For critical parts, an alternative LCSC part is noted in case of stock problems.

### Daisy Seed

- One standard Daisy Seed (not Daisy Field) is available. Revision: **Rev 5 (codec WM8731)**. The codec defines the full-scale levels of the whole analog input/output design. Design values from the datasheets (Daisy Seed v1.0.5, WM8731): ADC full scale 1.0 Vrms, absolute maximum ±1.8 V at the audio input pins, input resistance 20 kΩ min / 30 kΩ typ, and no series resistance or protection between the pin and the codec on the Seed. The full-scale level is verified by measurement (known sine in, dBFS read in firmware) before the values are final.
- Rev 5 has a known higher noise floor compared to other revisions, so the analog gain staging must drive the ADC as hot as possible without clipping. Upgrade path for a future main board revision: an external codec on the Daisy SAI.
- The Daisy Seed plugs into **2× female pin headers (1×20, 2.54 mm, THT)** so it can be removed. The row spacing is taken from the official Electrosmith footprint.

## System Architecture

- Processing: Daisy Seed, **48 kHz, 32-bit float**, block size about 48 samples (1 ms). 96 kHz is not used: the full effect chain would not fit in the CPU budget. Oversampling is used only inside the nonlinear stages (saturation, distortion).
- Signal flow: Input jacks → INST/LINE input stage + analog pre-amp gain → (bypass tap) → attenuating pad → Daisy Seed ADC → DSP effect chain → Daisy Seed DAC → output gain → bypass relay → master volume → balanced line outputs, and → headphone amplifier → headphone output.
- The electronics are split in two boards, plus a cosmetic front panel PCB:
  - **Main board (4-layer):** power supply, analog input stage, bypass relay, output stages, headphone amplifier, Daisy Seed.
  - **Control board (2-layer):** potentiometers, multiplexers, buttons, encoder, LEDs, LED driver. Connected to the main board with a ribbon cable (IDC connector) for the digital signals, and with separate analog cables for the three analog pots (see Potentiometers).
  - **Front panel PCB:** cosmetic panel (see Mechanical Structure and Front Panel).
- Reasons for the split (not size related): the main board will most likely need revisions (noise, gain staging), and can be re-made without re-soldering 40+ pots. Only the main board needs 4 layers, so the cost stays low. The LED and scanning currents stay physically away from the sensitive analog signals.

## Mechanical Structure and Front Panel

### Stack-up (top to bottom)

- **Front panel PCB:** graphics in silkscreen, holes for pots, buttons and encoder, windows for the LEDs. Held in place by the pot nuts.
- **Control board:** pots, encoder, buttons and LEDs soldered on it. Everything lines up with the front panel.
- **Main board:** at the bottom of the enclosure.
- **Removable bottom plate:** gives access to the Daisy Seed without taking the front panel apart.

### Daisy Seed Placement and Access

- The Daisy Seed sits on the **bottom side of the main board**, facing the bottom plate. It is placed where the routes are shortest and cleanest (audio pins toward the analog section, digital pins toward the control board connector), not at the board edge.
- **BOOT/RESET:** the Daisy Seed's own buttons, reached by removing the bottom plate. They must not be reachable by the user from outside. Free space is kept around them, with no tall parts or cables above them.
- **USB:** a short micro-USB to panel-mount extension (USB-C female on the rear panel preferred) for flashing firmware without opening the device. Space is kept for the plug on the main board.
- No tall components under or around the Daisy Seed.
- Rear panel: input jacks, output jacks, headphone jack (final position TBD at panel layout), DC jack, USB.

### LED Diffusion (Linear Light)

- The front panel PCB acts as the LED diffuser. Over each LED or LED strip there is a **copper-free window**. With **white soldermask** the light is diffused well (black soldermask blocks too much light).
- Over every meter strip the window is **one continuous rectangle**, so the meter looks like a linear light bar that fills up, not like separate dots.
- Between the control board and the panel (about 10 mm gap due to pot height) there is a **3D-printed black light guide** with one channel per strip or LED, to guide the light to its own window and prevent bleed into neighboring windows.
- A small test panel is made first to check the diffusion, color and brightness before the final panel.

### Panel Labels

- Pots that change function with the mode are labeled with both names: **ModeA name / ModeB name**. Parameters that are common to both modes have a single name. In a mode where a pot is not used, it is inactive.

## Power Supply

- Input: DC barrel jack 5.5 × 2.1 mm, accepts **9–15 V DC with either polarity** (polarity-correcting input stage), so almost any common 9 V or 12 V adapter works, including pedal adapters. Recommended: a generic **12 V adapter, at least 1 A**. The exact current rating is confirmed by the power budget calculation in the power design.
- No battery.
- Protection: resettable fuse (PTC) and overvoltage/transient protection (TVS).
- Internal rails:
  - Supply for the Daisy Seed (within its datasheet input range).
  - **±12 V for the analog section**, generated by a DC-DC converter, followed by LC filtering and low-noise regulators. This gives the headroom needed for hot studio line signals. Each rail stays within **±5 % (never above 12.6 V)**: the protection of the Daisy ADC input depends on it.
  - Separate 3.3 V rail for LEDs and logic, so the Daisy Seed's own regulator is not loaded, and a **5 V rail for the relay coils** (about 105 mA with all relays on: input 42 mA in INST mode, bypass 21 mA, output mute 42 mA).
- Grounding: single star point; analog and digital return currents kept separate in the layout.
- Outputs and headphones are muted during power-up and power-down (no pops): two relays in series with the outputs, released = muted, switched by an analog delay circuit that watches the supply. The Daisy is not involved.

## Input Section

- Two 6.35 mm TRS jacks: Left and Right input, with switch contacts (through-hole, from LCSC).
- A **global INST/LINE switch** sets the input type. The plug type (TS or TRS) does not tell the signal level (synths, keyboards and unbalanced line outputs use TS cables at line level), so automatic detection is not used.
  - **INST:** Left input only, unbalanced, **1 MΩ** input impedance, mono. The right channel always carries the left signal, in the analog path and in the DSP, even if something is plugged into the Right jack.
  - **LINE:** Left and Right, **balanced** (differential receiver, about 10–20 kΩ). Also works with TS (unbalanced) cables.
  - **Switching:** signal relays next to the input jacks (the high-impedance instrument signal must not travel to the panel). The panel toggle switches the relay coils directly: open = LINE (relays released), closed = INST. No Daisy pin and no firmware are involved. The three sources reach the relay through coupling capacitors, so both sides of every contact rest at 0 V and switching gives no DC step; any residual click is checked on the prototype.
  - **At power-on** the relays follow the toggle immediately. The outputs are muted during power-up anyway.
- **Mono in LINE mode:** done with the normalling contacts of the Right jack, without a relay. If nothing is plugged into the Right input, its tip and ring contacts connect the Right receiver input to the Left receiver input, so the right channel carries the left signal in the analog path. This works for the DSP and for the analog bypass. The Daisy does not need to know whether the source is mono, so there is no detection pin.
- Input protection: DC blocking, RF filtering, overvoltage clamping at the input stages.
- **ADC protection:** the analog chain runs at a high level and a resistive pad directly in front of the Daisy audio input brings it down to codec level. The pad limits the voltage at the pin (op-amp rail × divider ratio) and the current into the Seed (series resistor). No clamp diodes at the pin.
- Analog pre-amp gain: dual-gang pot (audio taper), not on the multiplexers, used as a passive attenuator followed by a fixed gain stage. The gain range must amplify weak instrument signals to a healthy level and attenuate hot line peaks (target up to about +20 dBu) below the ADC full scale. Target nominal level in the digital domain: about −18 dBFS.
- Provisional values, calculations and part choices are in `docs/input-section.md`. They are final after the codec full-scale level of the Rev 5 Seed and the op-amp output swing are measured.

## Global Bypass (A/B)

- One global bypass, for A/B comparison between the analog signal and the digital effect chain. Controlled by a panel button with LED.
- Implemented with a relay driven by a Daisy GPIO (the only Daisy pin of the output section). **Released = analog bypass**, so the main board passes audio without the Seed fitted or with a stopped firmware.
- **Buffered bypass:** the bypass signal is taken after the input stage and pre-amp, before the ADC pad, and goes to the output stage before the master volume. The DAC path gets a fixed gain of ×6.6 (+16.4 dB, the pad's two resistor values used the other way round), so both paths arrive at the relay at the same level. This way the A/B comparison is level-matched, a mono source comes out on both outputs, and both paths use the same master volume.
- No mute while the relay switches. Both sources reach the relay through coupling capacitors, so there is no DC step to switch. If the prototype shows an audible click, a firmware mute is added (one transistor, one Daisy pin).
- When the device is not powered, no signal passes. This is accepted.
- The per-effect On/Off buttons are digital, not true bypass (see Effect Chain).

## Master Output Section

### Master Stereo Out

- Two 6.35 mm TRS jacks, Left and Right, **balanced** (impedance-balanced). They also work with TS cables.
- Master volume: analog dual-gang pot after the DAC (keeps the noise floor low at low volume).
- Output meters: 2 vertical LED strips, 12 LEDs each, driven digitally from the DSP output. They show the level **before** the master volume (see Metering).
- Maximum output level: +18.6 dBu at 0 dBFS with the master volume fully up (bypass path: +18.9 dBu).

#### Parameters

- Main out Volume (analog)
- 2 LED strips: output level L-R

### Headphones Out

- One 6.35 mm stereo TRS jack (not a mini jack).
- Dedicated headphone driver for **32–300 Ω** headphones, with low output impedance (TI OPA1688, gain ×1).
- Own analog dual-gang volume pot.
- Muted at power-up and power-down.

#### Parameters

- HP Volume (analog)

## Controls and User Interface

### Potentiometers

- **40 digital pots: B10K linear**, read by the Daisy Seed through **5× 74HC4051** multiplexers (40 channels, all used).
- The response curves are applied in firmware: logarithmic for frequencies, times and ratios, linear in dB for gains. All values are smoothed to avoid zipper noise.
- **3 analog pots** (pre-amp gain, master volume, HP volume): dual-gang, audio taper, not on the multiplexers. They are mounted on the control board (the main board sits at the bottom of the enclosure and does not reach the panel) and connect to the main board with **short analog cables, separate from the digital ribbon**:
  - The pots are referenced to the main board's analog ground, carried in their own cable. They do not connect to the control board ground.
  - The pre-amp gain pot (input side) has its own cable: one ready-made shielded 3.5 mm stereo cable per channel between internal SMD jacks on the two boards. Master and HP volume (output side) share one separate 16-wire ribbon with a ground wire next to every signal wire (signals of several volts, followed by unity gain, so shielding is not needed). They never share a cable with the gain pot, so the output cannot leak back into the input.
  - The general ribbon carries only non-audio signals: LEDs, buttons, encoder, the INST/LINE toggle line (relay coil current), the 40 control pots and their multiplexers.

| Section | Digital pots |
|---|---|
| Pre-Amp | 1 |
| Compressor 1 | 5 |
| Distortion / Overdrive | 3 |
| 4-Band EQ | 12 |
| Compressor 2 | 5 |
| Chorus | 3 |
| Delay | 5 (+ encoder) |
| Reverb | 6 |
| **Total** | **40** |

### Buttons, Encoder and Switches

- Buttons, read through shift registers or an I2C expander:
  - 7 effect On/Off (Compressor 1, Distortion, EQ, Compressor 2, Chorus, Delay, Reverb)
  - 4 mode (Compressor 1, Distortion, Compressor 2, Chorus)
  - 4 chorus Dimension presets
  - 1 tap tempo
  - 1 global bypass
- 1 encoder with push (delay time / note modifier).
- 1 INST/LINE toggle switch. It switches the input relay coils directly (about 42 mA at 5 V) and is not read by the Daisy.
- Rule: circuits in the analog path are switched by panel switches, not by firmware. The only exception is the global bypass relay, because its control is a button with LED.

### LEDs

- All LEDs driven by I2C LED driver(s) on the control board.

| Indicator | LEDs |
|---|---|
| Input meters L-R (vertical) | 2 × 12 |
| Output meters L-R (vertical) | 2 × 12 |
| Gain reduction, Compressor 1 and 2 (horizontal) | 2 × 10 |
| Effect On/Off | 7 |
| Mode | 4 |
| Chorus presets | 4 |
| Chorus LFO rate | 1 |
| Delay subdivision (1/32, 1/16, 1/8, 1/4, 1/2) | 5 |
| Delay modifier (dotted, triplet) | 2 |
| Tap tempo | 1 |
| Global bypass | 1 |
| Power | 1 |
| **Total** | **94** |

### Metering

- All meters are driven digitally from the audio samples, so they show the real level in dBFS at the ADC/DAC. LED pitch 5 mm.
- **Input and output meters:** vertical, 12 LEDs (about 60 mm): −40, −30, −24, −18 (reference), −15, −12, −9, −6, −4, −2, −1, CLIP. Green up to −12, amber −9 to −4, red −2 to CLIP. Peak hold about 1 s.
- **Gain reduction meters** (both compressors): horizontal, 10 LEDs (about 50 mm): 1, 2, 3, 4, 5, 6, 8, 10, 14, 20 dB. Distressor-style: all off at 0 dB reduction, filling **from right to left** as the reduction increases. 1 dB steps in the first 6 dB, where most mixing work happens.

## Effect Chain (signal flow respectively)

Order: Pre-Amp → Compressor 1 → Distortion/Overdrive → 4-Band EQ → Compressor 2 → Chorus → Delay → Reverb.

#### General behavior

- Effect On/Off is digital: when an effect is off, the samples skip it. Switching uses a short crossfade (about 10 ms), so no clicks.
- Delay and Reverb keep their tails (trails) when they are switched off.
- Only the active mode of each effect runs. Mode switching is click-free. Both algorithms are prepared at startup.
- All parameter changes are smoothed.

### Pre-Amp

This is the first stage, where the signal from a Hi-Z or line-level source is pre-amplified and then saturated. The saturation should be colorful, not distorted. The gain knob only amplifies (or attenuates) the signal in the analog domain and does not saturate it. Only the Saturation pot saturates the signal, digitally, in the Daisy Seed.

The analog gain range must meet the Daisy Seed's ADC limits (see Input Section): it amplifies low-level signals and attenuates hot line signals so the ADC never clips. The input meters show the level after the pre-amp, exactly at the ADC (WE WANT A HEALTHY SIGNAL IN THE DIGITAL DOMAIN: NOT TOO HOT, NOT TOO WEAK, JUST PERFECT).

The digital saturation uses 2–4× oversampling and automatic level compensation, so the saturation amount changes the color, not the loudness.

#### Parameters

- Analog pre-amp gain (analog dual-gang pot)
- Saturation amount
- 2 LED strips: input level indicator L-R

### Compressor 1 (FET / Opto)

The first dynamics stage. Two modes, selected with the mode button; only one mode is active at a time.

- **FET mode** (1176-style behavior): threshold, ratio, attack, release, make-up gain. Fast FET-style attack and release (target ranges about 20 µs–800 µs attack, 50 ms–1.1 s release). The ratio pot is stepped: 4 / 8 / 12 / 20 / ALL (all-buttons mode).
- **Opto mode** (LA-2A-style behavior): Peak Reduction (on the Threshold pot) and Gain (on the Make-up pot), with program-dependent opto attack and release. Ratio, Attack and Release are inactive.
- Gain reduction meter: horizontal, 10 LEDs, Distressor-style (see Metering).

#### Parameters

- Compressor mode button (with LED)
- Threshold / Peak Reduction
- Ratio (FET mode only)
- Attack (FET mode only)
- Release (FET mode only)
- Make-up / Gain
- 1 LED strip: gain reduction
- Effect On/Off button

### Distortion / Overdrive

Two modes. Overdrive: soft, asymmetric clipping. Distortion: harder clipping with more gain. Both use oversampling to avoid aliasing.

#### Parameters

- Mode switch (with LED)
- Tone
- Drive / Dist amount
- Level
- Effect On/Off button

### 4-Band Parametric Equalizer

A 4-band EQ: Low-Shelf (20–200 Hz), Low-Mid peaking (80–900 Hz), High-Mid peaking (600–7000 Hz) and High-Shelf (1500–16000 Hz), with Gain (±15 dB), FC and Q (0.5–6) on every band. On the shelf bands, Q sets the shelf slope/resonance. FC pots use a logarithmic curve over the whole range. Filter coefficients are smoothed so sweeps are clean.

#### Parameters

- Low-Shelf:
  - Gain (±15 dB)
  - FC (20–200 Hz)
  - Q (0.5–6)
- Low-Mid:
  - Gain (±15 dB)
  - FC (80–900 Hz)
  - Q (0.5–6)
- High-Mid:
  - Gain (±15 dB)
  - FC (600–7000 Hz)
  - Q (0.5–6)
- High-Shelf:
  - Gain (±15 dB)
  - FC (1500–16000 Hz)
  - Q (0.5–6)
- Effect On/Off button

### Compressor 2 (VCA / Opto)

The second dynamics stage, after the EQ. Two modes, selected with the mode button; only one mode is active at a time.

- **VCA mode** (dbx 160-style behavior): Threshold, Compression (ratio) and Output Gain, with program-dependent attack and release. Attack and Release pots are inactive.
- **Opto mode** (Avalon AD2044-style behavior): Threshold, Compression (ratio), Attack, Release and Output Gain.
- Gain reduction meter: horizontal, 10 LEDs, Distressor-style, same as Compressor 1.

#### Parameters

- Compressor mode button (with LED)
- Threshold (common)
- Compression (common)
- Output Gain (common)
- Attack (Opto mode only)
- Release (Opto mode only)
- 1 LED strip: gain reduction
- Effect On/Off button

### Chorus

A dual-topology stereo chorus with two modes: an emulation of a dual bucket-brigade (BBD) anti-phase spatializer (Dimension mode) and a classic variable-parameter chorus (Stomp mode). Processing at 48 kHz, 32-bit float.

**Low-end integrity:** the dry signal is never filtered. Only the wet (modulated) path goes through a high-pass filter at 100 Hz (4th order) before the modulation. Below 100 Hz only the dry signal is heard, so there is no comb filtering or phase cancellation in the low end, and the stereo image of the bass is preserved on stereo mixes.

**Dimension mode:** two delay lines per channel (four in total: L(A), L(B), R(A), R(B)), cross-coupled with a feedback matrix, simulating 1024-stage BBD lines. Two LFOs with a triangle waveform in anti-phase (L(lfo) = −R(lfo)): when the left line pitches up, the right line pitches down by the same amount. The pitch modulations cancel out perceptually when the channels are heard together, so the result is a wide, static stereo field without audible pitch flutter. The four preset buttons select fixed LFO rates (0.25–0.6 Hz) and delay centers (5–15 ms).

**Stomp mode:** classic dual-mono / true-stereo chorus. The anti-phase constraint is removed, the LFO uses a sine or triangle waveform, and Rate and Depth are controlled by the pots. The preset values are not used.

**Indicators:** the preset buttons and the mode button have their own LEDs. One LED blinks at the LFO rate.

#### Parameters

- **Rate** (Stomp mode only): LFO speed, 0.1–10 Hz. In Dimension mode the preset values are used.
- **Depth** (Stomp mode only): delay modulation depth, 0.1–8.0 ms. In Dimension mode the preset values are used.
- **Mix / Width** (common):
  - Stomp mode (unity-dry injection): from 0.0 to 0.5 the dry signal stays at unity and the wet signal rises linearly from 0 to unity. At 0.5 both are at unity (maximum chorus density). From 0.5 to 1.0 the wet stays at unity and the dry falls linearly to 0. At 1.0 the output is 100% wet (pitch vibrato).
  - Dimension mode (cross-mix scaling): the dry signal stays at unity over the whole range. The knob only scales the cross-coupled delayed signals (L delay to R out and R delay to L out) from zero to their preset maximum. This widens or narrows the stereo image without ever lowering the mono center.
- **Dimension preset buttons 1–4** (Dimension mode only): fixed configurations. Several buttons can be active at the same time, combining their coefficients for higher modulation density (like the interlocked switches of the original unit).
- **Chorus mode button** (with LED): switches between Dimension and Stomp mode.
- Effect On/Off button

### Delay

A stereo, tempo-based delay.

- **Tempo:** set with the tap button (average of the last taps), range **60–200 BPM**. The tap LED blinks at the tempo.
- **Delay time:** the encoder steps through musical subdivisions **1/32, 1/16, 1/8, 1/4, 1/2** (maximum 1/2 note = 2 beats). Pushing the encoder cycles the modifier: normal → dotted → triplet. The selected subdivision is shown by 5 LEDs and the modifier by 2 LEDs (dotted, triplet).
- Maximum delay time: 1/2 dotted at 60 BPM = 3 s (fits easily in the Daisy Seed SDRAM).
- Delay time changes are smooth (no glitches when the tempo or subdivision changes).
- **Color:** a high-shelf cut filter **inside the feedback loop**, so every repeat gets darker than the previous one. Color FC sets the shelf frequency (proposed 1–12 kHz) and Color Cut sets the cut amount (proposed 0 to −18 dB).
- **Feedback:** with an internal safety limit, so the delay can never run away.
- **Stereo Width:** 0 = repeats in the center (mono), 1 = full ping-pong between left and right.
- **Dry/Wet:** unity-dry method (same algorithm as the chorus Stomp mode mix).

#### Parameters

- Delay time subdivision (encoder rotation)
- Normal / Dotted / Triplet (encoder push)
- Tap tempo button (with LED)
- Feedback
- Stereo Width
- Color FC
- Color Cut amount
- Dry/Wet
- Effect On/Off button

### Reverb

The reverb is based on the theory in this video: https://www.youtube.com/watch?v=6ZK2Goiyotk&t=2601s. It should sound very realistic and rich.

**Damping** is added: it sets how much faster the high frequencies decay compared to the low frequencies (frequency-dependent RT60, like the air and surface absorption in a real room). Without it, a reverb sounds metallic and unrealistic.

#### Parameters

- Reverberation time
- Damping
- Diffusion
- Size
- Pre-Delay
- Mix
- Effect On/Off button

## Firmware and Performance

- 48 kHz, 32-bit float, block size about 48 samples.
- CPU budget: with **all effects on at the same time**, the load must stay below about 75–80%. This is measured in Phase 0, before the hardware is fixed.
- Audio callback rules: no memory allocation, no blocking calls, no I/O. Controls, buttons and LEDs are handled outside the audio callback.
- Oversampling only in the nonlinear stages (saturation, distortion).
- Target latency input to output: below 3 ms.

## Implementation Phases

- **Phase 0, firmware feasibility on a bare Daisy Seed:** simple versions of all effects running together, to measure the CPU load. If the chain does not fit, it is found before any PCB is made.
- **Phase 1, main board:** power supply, input stage, bypass, outputs, headphones.
- **Phase 2, control board:** multiplexers, pots, buttons, LEDs, encoder.
- **Phase 3, effects:** each effect implemented and tuned one by one, at full quality.
- **Phase 4, enclosure and front panel:** panel layout, light guide, test panel, final front panel PCB.

## Open Items

- Measured full-scale level of the Rev 5 audio input/output, which defines the gain staging.
- First-board acceptance test before the Seed is fitted: measured op-amp output swing and voltage at the Daisy audio input pin (must stay inside ±1.8 V). Procedure in `docs/input-section.md`, section 11.1.
- Final gain and attenuation ranges and maximum input levels per mode (after the codec check).
- Hum pickup of the analog pot cables, checked on the prototype.
- Power budget, which defines the adapter current rating.
- Enclosure dimensions and front panel layout (position of every section and control).
- Light guide design, and panel color/diffusion test.
- Exact parameter ranges of the compressors, distortion and reverb, finalized during DSP implementation.
