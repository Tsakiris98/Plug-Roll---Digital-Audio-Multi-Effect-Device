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
                   top={2: ("global", "LINE_L_OUT"), 4: ("global", "INST_OUT"),
                        7: ("global", "LINE_R_OUT"), 5: ("global", "INST_OUT")},
                   bottom={3: ("global", "CH_L_IN"), 6: ("global", "CH_R_IN")})
    s.text("K1: Left tip to the LINE receiver or to the INST buffer.\nSecond contact set not used.", (180.34, 104.14))
    s.text("K2: each channel takes its LINE receiver or the INST buffer.", (241.3, 104.14))
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


def opamp_power(s, ref, value, fields, at, cpos, cneg):
    x, y = at
    u = s.add(NE5532, ref, value, at, unit=3, fields=fields, ref_at=(x + 3.81, y - 1.27), val_at=(x + 3.81, y + 1.27))
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

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "main-board.kicad_sch").write_text(root.render(root_page="1"))
    (OUT / "input-jacks.kicad_sch").write_text(jk.render())
    (OUT / "input.kicad_sch").write_text(inp.render())
    return EXPECT


if __name__ == "__main__":
    build()
    print("written:", OUT)
