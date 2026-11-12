#!/usr/bin/env python3
"""Builds the main-board schematic sheets (root + input section).

Run from the repository root with KiCad closed:
    python3 tools/schgen/main_board.py
Each run rewrites hardware/main-board/main-board.kicad_sch, input-jacks.kicad_sch
and input.kicad_sch. Do not edit those sheets by hand: change this script.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from kisch import Libraries, Sheet, uid  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "hardware" / "main-board"
PROJECT = "main-board"
ROOT_UUID = "2cce0cd6-b775-4f9e-a478-0bfadfac04cb"   # created by KiCad, kept

R01 = "JLCPCB:RT0603BRD0710KL"     # 10k 0.1 % thin film, C95204
C10U = "JLCPCB:CL31A106KBHNNNE"    # 10 uF 50 V X5R 1206, C13585
C100P = "JLCPCB:CL10C101JB8NNNC"   # 100 pF C0G 0603, C14858
C100N = "JLCPCB:CC0603KRX7R9BB104"  # 100 nF X7R 50 V 0603, C14663
BAV99 = "JLCPCB:BAV99,215"         # C2500
C100P_V = "100p C0G"
JACK = "JLCPCB:NMJ6HCD2"           # Neutrik 6.35 mm TRS, 3 normalling contacts, C368502
D4148 = "JLCPCB:1N4148W_C81598"    # pin 1 = cathode, pin 2 = anode
# The relay is drawn with KiCad's own symbol (coil and contacts are
# visible); footprint and LCSC number are those of the JLCPCB library part.
# G6K-2F-Y pins (Omron datasheet, terminal arrangement, top view): 1 = coil +,
# 8 = coil -, 3 and 6 = moving contacts, resting on 2 and 7, switching to 4 and 5.
RELAY = "Relay:G6K-2"
RELAY_FIELDS = {"Footprint": "JLCPCB:RELAY-SMD_G6K-2F-Y", "LCSC": "C2982926",
                "MPN": "G6K-2F-Y-5V", "Manufacturer": "Omron"}
R1K = "JLCPCB:0603WAF1001T5E"      # 1 k 1 %, C21190
R3K = "JLCPCB:0603WAF3001T5E"      # 3 k 1 %, C4211
R1M = "JLCPCB:0603WAF1004T5E"      # 1 M 1 %, C22935
R100 = "JLCPCB:0603WAF1000T5E"     # 100 R 1 %, C22775
R10K = "JLCPCB:0603WAF1002T5E"     # 10 k 1 %, C25804
R5K6 = "JLCPCB:0603WAF5601T5E"     # 5.6 k 1 %, C23189
R100K = "JLCPCB:0603WAF1003T5E"    # 100 k 1 %, C25803
C2N2 = "JLCPCB:0603CG222J500NT"    # 2.2 nF C0G 50 V, C2991172
JACK35 = "JLCPCB:PJ-327A5JJ"       # 3.5 mm stereo, SMD: 1, 2 = sleeve, 3 = ring, 4 = tip, 5 = tip switch
NMOS = "Transistor_FET:AO3400A"    # pin 1 = gate, 2 = source, 3 = drain
NMOS_FIELDS = {"Footprint": "JLCPCB:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR", "LCSC": "C20917",
               "MPN": "AO3400A", "Manufacturer": "AOS"}
TL072 = "Amplifier_Operational:TL072"
TL072_FIELDS = {"Footprint": "JLCPCB:SOIC-8_L5.0-W4.0-P1.27-LS6.0-BL", "LCSC": "C6961",
                "MPN": "TL072CDT", "Manufacturer": "STMicroelectronics"}
NE5532 = "Amplifier_Operational:NE5532"
NE5532_FIELDS = {"Footprint": "JLCPCB:SOIC-8_L4.9-W3.9-P1.27-LS6.0-BL", "LCSC": "C7426",
                 "MPN": "NE5532DR", "Manufacturer": "Texas Instruments"}

EXPECT = {}   # net name -> set of "REF.pin"; filled while drawing, checked against KiCad's netlist


def net(name, *pins):
    EXPECT.setdefault(name, set()).update(pins)


def line_receiver(s, ch, y0, unit, n):
    """Balanced line receiver, gain x0.5. ch = 'L' or 'R', y0 = vertical offset,
    n = first reference number offsets (dict)."""
    yc, yh = round(99.06 + y0, 2), round(127.0 + y0, 2)          # cold row (to the - input), hot row (to the + input)
    r, c, d = n["R"], n["C"], n["D"]
    hot, cold, out = f"LINE_{ch}_HOT", f"LINE_{ch}_COLD", f"LINE_{ch}_OUT"
    s.text(f"LINE receiver {ch}: balanced input, gain x0.5 (-6 dB). All resistors 10k 0.1 %.", (71.12, 48.26 + y0), 1.5)

    # ---- hot leg ----
    c1 = s.add(C10U, f"C{c}", "10u 50V", (99.06, yh))
    r1 = s.add(R01, f"R{r}", "10k 0.1%", (116.84, yh))
    d1 = s.add(BAV99, f"D{d}", "BAV99", (132.08, yh + 10.16), mirror="y", ref_at=(115.57, yh + 7.62), val_at=(115.57, yh + 10.16))
    r2 = s.add(R01, f"R{r+1}", "10k 0.1%", (149.86, yh + 10.16), rot=90)
    r3 = s.add(R01, f"R{r+2}", "10k 0.1%", (167.64, yh + 10.16), rot=90)
    c3 = s.add(C100P, f"C{c+2}", "100p C0G", (185.42, yh + 11.43), rot=90)
    s.glabel(hot, (71.12, yh), 180)
    s.wire((71.12, yh), c1.left)
    s.wire(c1.right, r1.left)
    # ---- cold leg ----
    c2 = s.add(C10U, f"C{c+1}", "10u 50V", (99.06, yc))
    r4 = s.add(R01, f"R{r+3}", "10k 0.1%", (116.84, yc))
    d2 = s.add(BAV99, f"D{d+1}", "BAV99", (132.08, yc - 10.16), rot=180, ref_at=(115.57, yc - 11.43), val_at=(115.57, yc - 8.89))
    s.glabel(cold, (71.12, yc), 180)
    s.wire((71.12, yc), c2.left)
    s.wire(c2.right, r4.left)
    # ---- op-amp (mirrored so that the - input is on top) ----
    u = s.add(NE5532, "U1", "NE5532", (215.9, 101.6 + y0), mirror="x", unit=unit, fields=NE5532_FIELDS,
              ref_at=(218.44, 107.95 + y0), val_at=(218.44, 110.49 + y0))
    pin_minus, pin_plus, pin_out = (2, 3, 1) if unit == 1 else (6, 5, 7)
    pm, pp, po = u.pin(pin_minus), u.pin(pin_plus), u.pin(pin_out)
    # hot node: R1 -> D1, R2, R3, C3 -> + input
    xup = 200.66
    s.wire(r1.right, (132.08, yh), (149.86, yh), (167.64, yh), (185.42, yh), (xup, yh), (xup, pp[1]), pp)
    for x in (132.08, 149.86, 167.64, 185.42):
        s.junction((x, yh))
    s.wire((149.86, yh), r2.top)
    s.wire((167.64, yh), r3.top)
    s.wire((185.42, yh), c3.top)
    for part in (r2, r3, c3):
        b = part.bottom
        s.wire(b, (b[0], b[1] + 2.54))
        s.power("GNDA", (b[0], b[1] + 2.54))
    assert d1.pin(3) == (132.08, yh), d1.pin(3)
    a, k = d1.pin(1), d1.pin(2)              # anode -> -12 V, cathode -> +12 V
    s.wire(a, (a[0], a[1] + 2.54))
    s.power("-12V", (a[0], a[1] + 2.54), rot=180)
    s.wire(k, (k[0], k[1] + 2.54), (k[0] - 10.16, k[1] + 2.54), (k[0] - 10.16, k[1] - 2.54))
    s.power("+12V", (k[0] - 10.16, k[1] - 2.54))
    # cold node: R4 -> D2 -> feedback rail -> - input
    xl, xr = 195.58, 231.14
    f1, f2, f3 = round(83.82 + y0, 2), round(71.12 + y0, 2), round(58.42 + y0, 2)
    s.wire(r4.right, (132.08, yc), (xl, yc), pm)
    s.junction((132.08, yc))
    s.junction((xl, yc))
    assert d2.pin(3) == (132.08, yc), d2.pin(3)
    a, k = d2.pin(1), d2.pin(2)
    s.wire(k, (k[0], k[1] - 2.54))
    s.power("+12V", (k[0], k[1] - 2.54))
    s.wire(a, (a[0], a[1] - 2.54), (a[0] + 10.16, a[1] - 2.54), (a[0] + 10.16, a[1] + 2.54))
    s.power("-12V", (a[0] + 10.16, a[1] + 2.54), rot=180)
    # feedback: two 10k in parallel (= 5k) and 100 pF
    r5 = s.add(R01, f"R{r+4}", "10k 0.1%", (213.36, f1))
    r6 = s.add(R01, f"R{r+5}", "10k 0.1%", (213.36, f2))
    c4 = s.add(C100P, f"C{c+3}", "100p C0G", (213.36, f3))
    s.wire((xl, yc), (xl, f1), (xl, f2), (xl, f3))
    s.wire(po, (xr, po[1]), (xr, f1), (xr, f2), (xr, f3))
    for part, y in ((r5, f1), (r6, f2), (c4, f3)):
        s.wire((xl, y), part.left)
        s.wire(part.right, (xr, y))
    for y in (f1, f2):
        s.junction((xl, y))
        s.junction((xr, y))
    s.junction((xr, po[1]))
    s.wire((xr, po[1]), (241.3, po[1]))
    s.glabel(out, (241.3, po[1]))

    U = "U1"
    net(hot, f"C{c}")
    net(f"{ch}_hot_a", f"C{c}", f"R{r}")
    net(f"{ch}_plus", f"R{r}", f"R{r+1}", f"R{r+2}", f"C{c+2}", f"D{d}.3", f"{U}.{pin_plus}")
    net("GNDA", f"R{r+1}", f"R{r+2}", f"C{c+2}")
    net(cold, f"C{c+1}")
    net(f"{ch}_cold_a", f"C{c+1}", f"R{r+3}")
    net(f"{ch}_minus", f"R{r+3}", f"R{r+4}", f"R{r+5}", f"C{c+3}", f"D{d+1}.3", f"{U}.{pin_minus}")
    net(out, f"R{r+4}", f"R{r+5}", f"C{c+3}", f"{U}.{pin_out}")
    net("+12V", f"D{d}.2", f"D{d+1}.2")
    net("-12V", f"D{d}.1", f"D{d+1}.1")

def rf_cap(s, ref, x, y):
    """100 pF from the point (x, y) on a horizontal wire down to analog ground."""
    c = s.add(C100P, ref, C100P_V, (x, y + 7.62), rot=90)
    s.junction((x, y))
    s.wire((x, y), c.top)
    b = c.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    net("GNDA", ref)


def input_jack(s, ref, yj, caps, tip, ring, tn, rn, sn):
    """One 6.35 mm TRS input jack. tip/ring/tn/rn/sn = ("global"|"local"|"gnd"|"nc", net name)."""
    xj = 60.96
    j = s.add(JACK, ref, "NMJ6HCD2", (xj, yj), mirror="y", ref_at=(xj, yj - 8.89), val_at=(xj, yj - 6.35))
    T, R, S, TN, RN, SN = (j.pin(k) for k in (1, 2, 3, 4, 5, 6))
    assert T == (67.31, round(yj - 2.54, 2)) and TN == (54.61, round(yj + 2.54, 2)), (T, TN)
    xe = 109.22

    def end(kind, name, at, rot):
        (s.glabel if kind == "global" else s.label)(name, at, rot)

    # tip: up and to the right, RF capacitor, label
    yt = round(yj - 22.86, 2)
    s.wire(T, (72.39, T[1]), (72.39, yt), (xe, yt))
    rf_cap(s, caps[0], 86.36, yt)
    end(tip[0], tip[1], (xe, yt), 0)
    net(tip[1], f"{ref}.1", caps[0])
    # ring: straight to the right, RF capacitor, label
    s.wire(R, (xe, R[1]))
    rf_cap(s, caps[1], 96.52, R[1])
    end(ring[0], ring[1], (xe, R[1]), 0)
    net(ring[1], f"{ref}.2", caps[1])
    # sleeve: analog ground
    s.wire(S, (72.39, S[1]), (72.39, S[1] + 5.08))
    s.power("GNDA", (72.39, S[1] + 5.08))
    net("GNDA", f"{ref}.3")
    # normalling contacts (closed while the jack is empty)
    xl = 44.45
    for pin_no, at, spec, dy in ((4, TN, tn, 7.62), (5, RN, rn, 0.0), (6, SN, sn, -7.62)):
        kind, name = spec
        if kind == "nc":
            s.no_connect(at)
            continue
        if kind == "gnd":
            continue
        y = round(RN[1] + dy, 2)
        s.wire(at, (49.53, at[1]), (49.53, y), (xl, y))
        end(kind, name, (xl, y), 180)
        net(name, f"{ref}.{pin_no}")
    if tn[0] == "gnd" and rn[0] == "gnd":
        s.wire(TN, (49.53, TN[1]), (49.53, TN[1] + 5.08))
        s.wire(RN, (49.53, RN[1]), (49.53, TN[1]))
        s.junction((49.53, TN[1]))
        s.power("GNDA", (49.53, TN[1] + 5.08))
        net("GNDA", f"{ref}.4", f"{ref}.5")


def relay(s, ref, x, y, top, bottom):
    """G6K-2F-Y. top = {pin: (kind, net)} for the fixed contacts 2, 4, 7, 5;
    bottom = the same for the moving contacts 3 and 6. Returns the coil pins (+, -)."""
    k = s.add(RELAY, ref, "G6K-2F-Y-5V", (x, y), fields=RELAY_FIELDS,
              ref_at=(x - 26.67, y - 1.27), val_at=(x - 26.67, y + 1.27))
    for pins, dy, rot in ((top, -5.08, 90), (bottom, 5.08, 270)):
        for n, spec in pins.items():
            at = k.pin(n)
            if spec is None:
                s.no_connect(at)
                continue
            kind, name = spec
            e = (at[0], round(at[1] + dy, 2))
            s.wire(at, e)
            (s.glabel if kind == "global" else s.label)(name, e, rot)
            net(name, f"{ref}.{n}")
    return k.pin(1), k.pin(8)


def jacks_and_switching(s):
    s.text("INPUT JACKS", (22.86, 20.32), 2.0)
    s.text("Tip = hot (+), ring = cold (-), sleeve = analog ground.\n"
           "TN / RN / SN are switch contacts that rest on T / R / S while the jack is empty.", (22.86, 27.94))
    s.text("LEFT input", (22.86, 38.1), 1.5)
    input_jack(s, "J1", 63.5, ("C11", "C12"),
               tip=("local", "L_TIP"), ring=("global", "LINE_L_COLD"),
               tn=("gnd", ""), rn=("gnd", ""), sn=("nc", ""))
    s.text("Empty jack: tip and ring are grounded (silent input).", (22.86, 86.36))
    s.text("RIGHT input", (22.86, 99.06), 1.5)
    input_jack(s, "J2", 129.54, ("C13", "C14"),
               tip=("global", "LINE_R_HOT"), ring=("global", "LINE_R_COLD"),
               tn=("global", "LINE_L_HOT"), rn=("global", "LINE_L_COLD"), sn=("nc", ""))
    s.text("Empty jack: the Right receiver gets the Left signal (mono).\n"
           "Purely analog, the Daisy is not involved.", (22.86, 157.48))

    s.text("INST / LINE SWITCHING", (144.78, 20.32), 2.0)
    s.text("Relays drawn released (no coil current) = LINE. Panel toggle closed = coils on = INST.", (144.78, 25.4))
    yk = 68.58
    p1, m1 = relay(s, "K1", 187.96, yk,
                   top={2: ("global", "LINE_L_HOT"), 4: ("global", "INST_IN"), 7: None, 5: None},
                   bottom={3: ("local", "L_TIP"), 6: None})
    p2, m2 = relay(s, "K2", 248.92, yk,
                   top={2: ("local", "LINE_L_AC"), 4: ("local", "INST_AC"),
                        7: ("local", "LINE_R_AC"), 5: ("local", "INST_AC")},
                   bottom={3: ("global", "CH_L_IN"), 6: ("global", "CH_R_IN")})
    s.text("K1: Left tip to the LINE receiver or to the INST buffer.\nSecond contact set not used.", (180.34, 104.14))
    s.text("K2: each channel takes its LINE receiver or the INST buffer.", (241.3, 104.14))
    # coupling capacitors in front of K2: both sides of every contact rest at 0 V DC
    s.text("Coupling capacitors in front of K2", (304.8, 43.18), 1.5)
    s.text("The three sources reach K2 without their DC offset,\nso switching INST / LINE gives no DC step (click).", (304.8, 134.62))
    for i, (src, dst) in enumerate((("LINE_L_OUT", "LINE_L_AC"), ("LINE_R_OUT", "LINE_R_AC"), ("INST_OUT", "INST_AC"))):
        ac_couple(s, src, dst, f"C{28 + i}", f"R{29 + i}", 320.04, 55.88 + 22.86 * i)
    # coils: + to 5 V, - to the panel toggle (which closes to ground). No transistor, no Daisy pin.
    yr = 127.0
    for p in (p1, p2):
        s.wire(p, (p[0], p[1] - 5.08))
        s.power("+5V", (p[0], p[1] - 5.08))
    xe = 139.7
    s.wire(m2, (m2[0], yr), (m1[0], yr), (165.1, yr), (xe, yr))
    s.wire(m1, (m1[0], yr))
    s.junction((m1[0], yr))
    s.junction((165.1, yr))
    s.glabel("INST_SW", (xe, yr), 180)
    d = s.add(D4148, "D5", "1N4148W", (165.1, yr - 10.16), rot=270, ref_at=(172.72, yr - 11.43), val_at=(172.72, yr - 8.89))
    kk, aa = d.pin(1), d.pin(2)
    assert kk[1] < aa[1], (kk, aa)            # cathode on top, to +5 V
    s.wire(aa, (165.1, yr))
    s.wire(kk, (kk[0], kk[1] - 2.54))
    s.power("+5V", (kk[0], kk[1] - 2.54))
    s.text("INST_SW goes through the ribbon to the INST/LINE toggle on the control board.\n"
           "Toggle open = LINE. Toggle closed to ground = both coils on = INST.\n"
           "D5 absorbs the voltage spike of the coils when the toggle opens.", (114.3, 139.7))
    # 5 V decoupling next to the relays
    cd = s.add(C100N, "C15", "100n", (210.82, yr + 12.7), rot=90)
    t_, b_ = cd.top, cd.bottom
    s.wire(t_, (t_[0], t_[1] - 2.54))
    s.power("+5V", (t_[0], t_[1] - 2.54))
    s.wire(b_, (b_[0], b_[1] + 2.54))
    s.power("GND", (b_[0], b_[1] + 2.54))
    s.text("5 V decoupling, placed at the relays", (226.06, yr + 13.97))

    net("+5V", "K1.1", "K2.1", "D5.1", "C15.2")
    net("INST_SW", "K1.8", "K2.8", "D5.2")
    net("GND", "C15.1")

def inst_buffer(s):
    """Instrument input: 1 Mohm, gain x4 (+12 dB), TL072."""
    y = 101.6
    s.text("INST BUFFER", (38.1, 60.96), 2.0)
    s.text("Instrument (guitar) input, used only in INST mode. Input resistance 1 Mohm, gain x4 (+12 dB) = 1 + R15/R16.",
           (38.1, 68.58))
    s.glabel("INST_IN", (50.8, y), 180)
    r13 = s.add(R1K, "R13", "1k", (66.04, y))
    s.wire((50.8, y), r13.left)
    c17 = s.add(C100N, "C17", "100n", (96.52, y))
    s.wire(r13.right, c17.left)
    rf_cap(s, "C16", 81.28, y)
    u = s.add(TL072, "U2", "TL072", (170.18, y + 2.54), unit=1, fields=TL072_FIELDS,
              ref_at=(177.8, y - 5.08), val_at=(177.8, y - 2.54))
    pp, pm, po = u.pin(3), u.pin(2), u.pin(1)
    assert pp == (162.56, y) and pm == (162.56, round(y + 5.08, 2)), (pp, pm)
    s.wire(c17.right, (111.76, y), (139.7, y), pp)
    # 1 Mohm to ground: sets the input resistance and the DC level of the op-amp input
    r14 = s.add(R1M, "R14", "1M", (111.76, y + 7.62), rot=90)
    s.junction((111.76, y))
    s.wire((111.76, y), r14.top)
    b = r14.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    # clamp to the rails, directly at the op-amp input
    d = s.add(BAV99, "D6", "BAV99", (139.7, y + 10.16), mirror="y", ref_at=(125.73, y + 7.62), val_at=(125.73, y + 10.16))
    assert d.pin(3) == (139.7, y), d.pin(3)
    s.junction((139.7, y))
    a, k = d.pin(1), d.pin(2)              # anode -> -12 V, cathode -> +12 V
    s.wire(a, (a[0], a[1] + 2.54))
    s.power("-12V", (a[0], a[1] + 2.54), rot=180)
    s.wire(k, (k[0], k[1] + 2.54), (k[0] - 10.16, k[1] + 2.54), (k[0] - 10.16, k[1] - 2.54))
    s.power("+12V", (k[0] - 10.16, k[1] - 2.54))
    # output and feedback
    xo, yf = 187.96, y + 20.32
    s.wire(po, (xo, po[1]), (198.12, po[1]))
    s.junction((xo, po[1]))
    s.glabel("INST_OUT", (198.12, po[1]))
    r15 = s.add(R3K, "R15", "3k", (172.72, yf))
    s.wire((xo, po[1]), (xo, yf), r15.right)
    xm = 157.48
    s.wire(r15.left, (xm, yf), (xm, pm[1]), pm)
    s.junction((xm, yf))
    r16 = s.add(R1K, "R16", "1k", (xm, yf + 7.62), rot=90)
    s.wire((xm, yf), r16.top)
    b = r16.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    s.text("R13 limits the current of an overvoltage, C16 shorts radio frequencies,\n"
           "C17 blocks DC from the source, D6 keeps the op-amp input inside the +/-12 V rails.", (38.1, 147.32))
    # second half of U2: not used, wired as a follower of ground so it stays quiet
    s.text("Unused half of U2", (220.98, 91.44), 1.5)
    u2 = s.add(TL072, "U2", "TL072", (238.76, y + 2.54), unit=2, fields=TL072_FIELDS,
               ref_at=(246.38, y - 5.08), val_at=(246.38, y - 2.54))
    p5, p6, p7 = u2.pin(5), u2.pin(6), u2.pin(7)
    s.wire(p5, (223.52, p5[1]), (223.52, p5[1] + 2.54))
    s.power("GNDA", (223.52, p5[1] + 2.54))
    s.wire(p6, (228.6, p6[1]), (228.6, y + 17.78), (251.46, y + 17.78), (251.46, p7[1]), p7)
    s.text("U2 supply and decoupling", (269.24, 96.52), 1.5)
    opamp_power(s, "U2", "TL072", TL072_FIELDS, (276.86, 119.38), "C18", "C19", lib=TL072)

    net("INST_IN", "R13")
    net("inst_a", "R13", "C16", "C17")
    net("inst_plus", "C17", "R14", "D6.3", "U2.3")
    net("GNDA", "R14", "R16", "U2.5")
    net("inst_fb", "U2.2", "R15", "R16")
    net("INST_OUT", "U2.1", "R15")
    net("inst_spare", "U2.6", "U2.7")
    net("+12V", "D6.2")
    net("-12V", "D6.1")

def to_ground(s, part_lib, ref, value, x, y, name=None):
    """Two-pin part from the point (x, y) on a horizontal wire down to analog ground."""
    part = s.add(part_lib, ref, value, (x, y + 7.62), rot=90)
    s.junction((x, y))
    s.wire((x, y), part.top)
    b = part.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    net("GNDA", ref)
    return part


def gain_stage(s, ch, yj, unit, jref, r, c, adc_pin):
    """Gain pot connector, fixed gain x11, pad to the Daisy ADC. r, c = first R and C numbers."""
    R = lambda i: f"R{r + i}"
    C = lambda i: f"C{c + i}"
    s.text(f"{'LEFT' if ch == 'L' else 'RIGHT'} channel: gain pot, x11 (+20.8 dB), pad to the Daisy", (38.1, yj - 20.32), 1.5)
    # --- cable to the gain pot on the control board ---
    j = s.add(JACK35, jref, "PJ-327A", (60.96, yj), ref_at=(58.42, yj - 16.51), val_at=(58.42, yj - 13.97))
    p1, p2, p3, p4, p5 = (j.pin(k) for k in (1, 2, 3, 4, 5))
    assert p3 == (66.04, round(yj - 1.27, 2)) and p4 == (66.04, round(yj + 3.81, 2)), (p3, p4)
    s.no_connect(p5)
    yg = round(yj + 11.43, 2)
    s.wire(p1, (68.58, p1[1]), (68.58, yj - 10.16), (50.8, yj - 10.16), (50.8, yg))
    s.wire(p2, (68.58, p2[1]), (68.58, yg), (50.8, yg), (50.8, yg + 2.54))
    s.junction((50.8, yg))
    s.power("GNDA", (50.8, yg + 2.54))
    yt = round(yj + 27.94, 2)
    s.glabel(f"CH_{ch}_IN", (40.64, yt), 180)
    r17 = s.add(R100, R(0), "100R", (55.88, yt))
    s.wire((40.64, yt), r17.left)
    s.wire(r17.right, (73.66, yt), (73.66, p4[1]), p4)
    s.text("Cable to the gain pot: tip = top of the pot, ring = wiper, sleeve = analog ground + shield.", (38.1, yj + 38.1))
    # --- wiper to the op-amp ---
    uy = round(yj + 1.27, 2)
    u = s.add(NE5532, "U3", "NE5532", (139.7, uy), unit=unit, fields=NE5532_FIELDS,
              ref_at=(147.32, uy - 7.62), val_at=(147.32, uy - 5.08))
    pin_minus, pin_plus, pin_out = (2, 3, 1) if unit == 1 else (6, 5, 7)
    pm, pp, po = u.pin(pin_minus), u.pin(pin_plus), u.pin(pin_out)
    assert pp[1] == p3[1], (pp, p3)
    s.wire(p3, pp)
    to_ground(s, R100K, R(1), "100k", 91.44, p3[1])
    rf_cap(s, C(0), 106.68, p3[1])
    # --- feedback: 10k / 1k = x11, 100 pF across the 10k ---
    xm, xo = 127.0, 157.48
    y1, y2 = round(uy + 20.32, 2), round(uy + 30.48, 2)
    rf = s.add(R10K, R(2), "10k", (142.24, y1))
    cf = s.add(C100P, C(1), C100P_V, (142.24, y2))
    s.wire(pm, (xm, pm[1]), (xm, y1), (xm, y2), cf.left)
    s.wire((xm, y1), rf.left)
    s.wire(po, (xo, po[1]), (xo, y1), (xo, y2), cf.right)
    s.wire(rf.right, (xo, y1))
    for pt in ((xm, y1), (xo, y1), (xo, po[1])):
        s.junction(pt)
    rg = s.add(R1K, R(3), "1k", (114.3, y1 + 7.62), rot=90)
    s.wire((xm, y1), (114.3, y1), rg.top)
    b = rg.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    # --- hot node: bypass tap, then the pad ---
    xh = 172.72
    s.wire((xo, po[1]), (xh, po[1]))
    s.junction((xh, po[1]))
    s.wire((xh, po[1]), (xh, po[1] - 12.7), (185.42, po[1] - 12.7))
    s.glabel(f"HOT_{ch}", (185.42, po[1] - 12.7))
    s.text("hot node: 0 dBFS = +18.9 dBu here. Bypass tap.", (172.72, po[1] - 17.78))
    rs = s.add(R5K6, R(4), "5k6", (187.96, po[1]))
    s.wire((xh, po[1]), rs.left)
    xe = 236.22
    s.wire(rs.right, (xe, po[1]))
    to_ground(s, R1K, R(5), "1k", 205.74, po[1])
    to_ground(s, C2N2, C(2), "2n2 C0G", 220.98, po[1])
    s.glabel(f"ADC_IN_{ch}", (xe, po[1]))
    s.text(f"to Daisy Seed pin {adc_pin}", (236.22, po[1] + 5.08))

    net(f"CH_{ch}_IN", R(0))
    net(f"{ch}_pot_top", R(0), f"{jref}.4")
    net("GNDA", f"{jref}.1", f"{jref}.2", R(3))
    net(f"{ch}_wiper", f"{jref}.3", R(1), C(0), f"U3.{pin_plus}")
    net(f"{ch}_gain_fb", f"U3.{pin_minus}", R(2), C(1), R(3))
    net(f"HOT_{ch}", f"U3.{pin_out}", R(2), C(1), R(4))
    net(f"ADC_IN_{ch}", R(4), R(5), C(2))


def input_gain(s):
    s.text("INPUT GAIN AND ADC PAD", (38.1, 25.4), 2.0)
    s.text("The gain pot (10k dual, audio taper) is on the control board. One shielded 3.5 mm stereo cable per channel connects it to J3 / J4.\n"
           "Pad 5k6 / 1k brings the hot node down to codec level and limits voltage and current at the Daisy pin. No bias: the Seed has its own input capacitor.",
           (38.1, 33.02))
    gain_stage(s, "L", 66.04, 1, "J3", 17, 20, 16)
    gain_stage(s, "R", 167.64, 2, "J4", 23, 23, 17)
    s.text("U3 supply and decoupling", (279.4, 96.52), 1.5)
    opamp_power(s, "U3", "NE5532", NE5532_FIELDS, (287.02, 119.38), "C26", "C27")

def ac_couple(s, src, dst, cref, rref, x, y, src_kind="global"):
    """src label -> 10 uF -> (100k to ground) -> dst local label."""
    (s.glabel if src_kind == "global" else s.label)(src, (x, y), 180)
    c = s.add(C10U, cref, "10u 50V", (x + 15.24, y))
    s.wire((x, y), c.left)
    s.wire(c.right, (x + 43.18, y))
    to_ground(s, R100K, rref, "100k", x + 30.48, y)
    s.label(dst, (x + 43.18, y))
    net(src, cref)
    net(dst, cref, rref)


def dac_stage(s, ch, y, unit, r, c, pin):
    """Daisy DAC output -> x6.6 -> coupling capacitor -> DSP_<ch> (to the bypass relay)."""
    R = lambda i: f"R{r + i}"
    C = lambda i: f"C{c + i}"
    s.text(f"{'LEFT' if ch == 'L' else 'RIGHT'} channel: DAC gain x6.6 (+16.4 dB) = 1 + 5k6 / 1k", (38.1, y - 17.78), 1.5)
    s.glabel(f"DAC_OUT_{ch}", (48.26, y), 180)
    s.text(f"from Daisy Seed pin {pin}", (27.94, y + 5.08))
    u = s.add(NE5532, "U4", "NE5532", (99.06, y + 2.54), unit=unit, fields=NE5532_FIELDS,
              ref_at=(106.68, y - 5.08), val_at=(106.68, y - 2.54))
    pin_minus, pin_plus, pin_out = (2, 3, 1) if unit == 1 else (6, 5, 7)
    pm, pp, po = u.pin(pin_minus), u.pin(pin_plus), u.pin(pin_out)
    assert pp == (91.44, y), pp
    s.wire((48.26, y), pp)
    to_ground(s, R100K, R(0), "100k", 66.04, y)
    xm, xo = 86.36, 116.84
    y1, y2 = round(y + 22.86, 2), round(y + 33.02, 2)
    rf = s.add(R5K6, R(1), "5k6", (101.6, y1))
    cf = s.add(C100P, C(0), C100P_V, (101.6, y2))
    s.wire(pm, (xm, pm[1]), (xm, y1), (xm, y2), cf.left)
    s.wire((xm, y1), rf.left)
    s.wire(po, (xo, po[1]), (xo, y1), (xo, y2), cf.right)
    s.wire(rf.right, (xo, y1))
    for pt in ((xm, y1), (xo, y1), (xo, po[1])):
        s.junction(pt)
    rg = s.add(R1K, R(2), "1k", (73.66, y1 + 7.62), rot=90)
    s.wire((xm, y1), (73.66, y1), rg.top)
    b = rg.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GNDA", (b[0], b[1] + 2.54))
    cc = s.add(C10U, C(1), "10u 50V", (132.08, po[1]))
    s.wire((xo, po[1]), cc.left)
    s.wire(cc.right, (160.02, po[1]))
    to_ground(s, R100K, R(3), "100k", 147.32, po[1])
    s.label(f"DSP_{ch}", (160.02, po[1]))
    net(f"DAC_OUT_{ch}", R(0), f"U4.{pin_plus}")
    net("GNDA", R(2))
    net(f"{ch}_dac_fb", f"U4.{pin_minus}", R(1), C(0), R(2))
    net(f"{ch}_dac_amp", f"U4.{pin_out}", R(1), C(0), C(1))
    net(f"DSP_{ch}", C(1), R(3))


def output_dac(s):
    s.text("DAC GAIN AND GLOBAL BYPASS", (38.1, 25.4), 2.0)
    s.text("The Daisy output (1.0 Vrms at 0 dBFS) is amplified to the level of the hot node, so the effect path and the analog bypass path\n"
           "reach the bypass relay at the same level. No bias: the Seed has its own output capacitor.", (38.1, 33.02))
    dac_stage(s, "L", 71.12, 1, 32, 31, 18)
    dac_stage(s, "R", 167.64, 2, 36, 33, 19)
    # bypass sources from the input section
    s.text("Analog bypass signal from the input section", (203.2, 162.56), 1.5)
    ac_couple(s, "HOT_L", "BYP_L", "C35", "R40", 220.98, 175.26)
    ac_couple(s, "HOT_R", "BYP_R", "C36", "R41", 220.98, 198.12)
    # relay
    s.text("BYPASS RELAY. Drawn released (no coil current) = analog bypass. BYPASS_RELAY high = effect path.", (203.2, 50.8), 1.5)
    yk = 83.82
    p1, m1 = relay(s, "K3", 279.4, yk,
                   top={2: ("local", "BYP_L"), 4: ("local", "DSP_L"), 7: ("local", "BYP_R"), 5: ("local", "DSP_R")},
                   bottom={3: ("global", "OUT_SEL_L"), 6: ("global", "OUT_SEL_R")})
    s.wire(p1, (p1[0], p1[1] - 5.08))
    s.power("+5V", (p1[0], p1[1] - 5.08))
    yr = round(yk + 40.64, 2)
    xd, xq = round(m1[0] - 12.7, 2), round(m1[0] - 20.32, 2)
    s.wire(m1, (m1[0], yr), (xd, yr), (xq, yr))
    s.junction((xd, yr))
    d = s.add(D4148, "D7", "1N4148W", (xd, yr - 10.16), rot=270, ref_at=(xd + 7.62, yr - 11.43), val_at=(xd + 7.62, yr - 8.89))
    kk, aa = d.pin(1), d.pin(2)
    assert kk[1] < aa[1], (kk, aa)
    s.wire(aa, (xd, yr))
    s.wire(kk, (kk[0], kk[1] - 2.54))
    s.power("+5V", (kk[0], kk[1] - 2.54))
    q1 = s.add(NMOS, "Q1", "AO3400A", (xq - 2.54, yr + 10.16), fields=NMOS_FIELDS,
               ref_at=(xq + 10.16, yr + 8.89), val_at=(xq + 10.16, yr + 11.43))
    g, src, drn = q1.pin(1), q1.pin(2), q1.pin(3)
    assert drn[0] == xq and drn[1] < src[1], (g, src, drn)
    s.wire((xq, yr), drn)
    s.wire(src, (src[0], src[1] + 2.54))
    s.power("GND", (src[0], src[1] + 2.54))
    xg = round(g[0] - 5.08, 2)
    s.wire(g, (xg, g[1]))
    s.junction((xg, g[1]))
    rpd = s.add(R100K, "R43", "100k", (xg, g[1] + 7.62), rot=90)
    s.wire((xg, g[1]), rpd.top)
    b = rpd.bottom
    s.wire(b, (b[0], b[1] + 2.54))
    s.power("GND", (b[0], b[1] + 2.54))
    rg = s.add(R100, "R42", "100R", (xg - 10.16, g[1]))
    s.wire(rg.right, (xg, g[1]))
    l = rg.left
    s.wire(l, (l[0] - 5.08, l[1]))
    s.glabel("BYPASS_RELAY", (l[0] - 5.08, l[1]), 180)
    s.text("R43 keeps the transistor off until the Daisy drives the line: at power-on, in reset and\n"
           "with the Seed removed the relay stays released = bypass. D7 absorbs the coil's switch-off spike.", (289.56, yr + 12.7))
    cd = s.add(C100N, "C39", "100n", (350.52, 81.28), rot=90)
    t_, b_ = cd.top, cd.bottom
    s.wire(t_, (t_[0], t_[1] - 2.54))
    s.power("+5V", (t_[0], t_[1] - 2.54))
    s.wire(b_, (b_[0], b_[1] + 2.54))
    s.power("GND", (b_[0], b_[1] + 2.54))
    s.text("5 V decoupling at K3", (365.76, 82.55))
    s.text("U4 supply and decoupling", (332.74, 180.34), 1.5)
    opamp_power(s, "U4", "NE5532", NE5532_FIELDS, (340.36, 203.2), "C37", "C38")
    net("+5V", "K3.1", "D7.1", "C39.2")
    net("bypass_drv", "K3.8", "D7.2", "Q1.3")
    net("GND", "Q1.2", "R43", "C39.1")
    net("q1_gate", "Q1.1", "R42", "R43")
    net("BYPASS_RELAY", "R42")


def opamp_power(s, ref, value, fields, at, cpos, cneg, lib=NE5532):
    x, y = at
    u = s.add(lib, ref, value, at, unit=3, fields=fields, ref_at=(x + 3.81, y - 1.27), val_at=(x + 3.81, y + 1.27))
    vp, vn = u.pin(8), u.pin(4)
    xc = x + 12.7
    c1 = s.add(C100N, cpos, "100n", (xc, vp[1] - 2.54 + 5.08), rot=90)
    c2 = s.add(C100N, cneg, "100n", (xc, vp[1] - 2.54 + 15.24), rot=90)
    top, mid, bot = c1.top, c1.bottom, c2.bottom
    assert c2.top == mid
    s.wire(vp, (vp[0], top[1]), (xc, top[1]))
    s.wire((vp[0], top[1]), (vp[0], top[1] - 2.54))
    s.junction((vp[0], top[1]))
    s.power("+12V", (vp[0], top[1] - 2.54))
    s.wire(vn, (vn[0], bot[1]), (xc, bot[1]))
    s.wire((vn[0], bot[1]), (vn[0], bot[1] + 2.54))
    s.junction((vn[0], bot[1]))
    s.power("-12V", (vn[0], bot[1] + 2.54), rot=180)
    s.wire(mid, (xc + 15.24, mid[1]), (xc + 15.24, mid[1] + 2.54))
    s.junction(mid)
    s.power("GNDA", (xc + 15.24, mid[1] + 2.54))
    net("+12V", f"{ref}.8", cpos)
    net("-12V", f"{ref}.4", cneg)
    net("GNDA", cpos, cneg)


def build():
    EXPECT.clear()
    libs = Libraries()
    root_path = "/" + ROOT_UUID
    root = Sheet(libs, PROJECT, root_path, paper="A4", title="Plug & Roll - Main board", rev="0.1", file_uuid=ROOT_UUID)
    root.text("Plug & Roll main board. Each block of the board is one sub-sheet.", (25.4, 25.4), 2.0)
    jk_uuid = root.subsheet("Input jacks and switching", "input-jacks.kicad_sch", (25.4, 38.1), (50.8, 25.4), "2")
    in_uuid = root.subsheet("Input receivers", "input.kicad_sch", (101.6, 38.1), (50.8, 25.4), "3")

    jk = Sheet(libs, PROJECT, root_path + "/" + jk_uuid, paper="A3",
               title="Plug & Roll - Main board - Input jacks and INST/LINE switching", rev="0.1",
               file_uuid=uid("file", "input-jacks"), pwr_base=100)
    jacks_and_switching(jk)

    inp = Sheet(libs, PROJECT, root_path + "/" + in_uuid, paper="A3",
                title="Plug & Roll - Main board - Input receivers", rev="0.1",
                file_uuid=uid("file", "input"))
    line_receiver(inp, "L", 0.0, 1, {"R": 1, "C": 1, "D": 1})
    line_receiver(inp, "R", 111.76, 2, {"R": 7, "C": 5, "D": 3})
    inp.text("U1 supply and decoupling", (269.24, 96.52), 1.5)
    opamp_power(inp, "U1", "NE5532", NE5532_FIELDS, (276.86, 119.38), "C9", "C10")

    it_uuid = root.subsheet("INST buffer", "input-inst.kicad_sch", (177.8, 38.1), (50.8, 25.4), "4")
    it = Sheet(libs, PROJECT, root_path + "/" + it_uuid, paper="A3",
               title="Plug & Roll - Main board - INST buffer", rev="0.1",
               file_uuid=uid("file", "input-inst"), pwr_base=200)
    inst_buffer(it)
    (OUT / "input-inst.kicad_sch").write_text(it.render())

    gn_uuid = root.subsheet("Input gain and ADC pad", "input-gain.kicad_sch", (25.4, 76.2), (50.8, 25.4), "5")
    gn = Sheet(libs, PROJECT, root_path + "/" + gn_uuid, paper="A3",
               title="Plug & Roll - Main board - Input gain and ADC pad", rev="0.1",
               file_uuid=uid("file", "input-gain"), pwr_base=300)
    input_gain(gn)
    (OUT / "input-gain.kicad_sch").write_text(gn.render())

    od_uuid = root.subsheet("DAC gain and bypass", "output-dac.kicad_sch", (101.6, 76.2), (50.8, 25.4), "6")
    od = Sheet(libs, PROJECT, root_path + "/" + od_uuid, paper="A3",
               title="Plug & Roll - Main board - DAC gain and global bypass", rev="0.1",
               file_uuid=uid("file", "output-dac"), pwr_base=400)
    output_dac(od)
    (OUT / "output-dac.kicad_sch").write_text(od.render())

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "main-board.kicad_sch").write_text(root.render(root_page="1"))
    (OUT / "input-jacks.kicad_sch").write_text(jk.render())
    (OUT / "input.kicad_sch").write_text(inp.render())
    return EXPECT


if __name__ == "__main__":
    build()
    print("written:", OUT)
