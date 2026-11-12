#!/usr/bin/env python3
"""Regenerates the main-board sheets, exports KiCad's netlist and compares it
with the intended connections declared in main_board.py.

    python3 tools/schgen/verify.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import main_board  # noqa: E402
from kisch import KICAD_CLI  # noqa: E402


def kicad_nets(root):
    out = Path(tempfile.mkdtemp()) / "out.net"
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(out), str(root)],
                   check=True, capture_output=True)
    t = out.read_text()
    nets = {}
    for blk in re.split(r'\(net\s+\(code', t)[1:]:
        name = re.search(r'\(name "([^"]*)"', blk).group(1)
        nets[name] = set(f"{r}.{p}" for r, p in re.findall(r'\(node\s*\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', blk))
    return nets


def main():
    expect = main_board.build()
    nets = kicad_nets(main_board.OUT / "main-board.kicad_sch")
    pin_net = {p: n for n, ps in nets.items() for p in ps}
    errors = []
    # 1) pins given explicitly ("U1.3") must be on one net together, per expected net
    # 2) two-pin parts given without pin ("R1") must have exactly one pin on that net
    groups = {}
    for ename, members in expect.items():
        found = set()
        for m in members:
            if "." in m:
                found.add(pin_net.get(m, f"<{m} unconnected>"))
            else:
                cands = {pin_net.get(f"{m}.{k}") for k in ("1", "2")}
                found.add(tuple(sorted(x or "<none>" for x in cands)))
        groups[ename] = (members, found)
    for ename, (members, found) in groups.items():
        # resolve: there must be one KiCad net common to every member
        common = None
        for f in found:
            s = {f} if isinstance(f, str) else set(f)
            common = s if common is None else common & s
        if not common:
            errors.append(f"{ename}: members are not on one net: {sorted(map(str, found))}")
            continue
        knet = sorted(common)[0]
        want = len(members)
        have = nets[knet]
        # every pin on the KiCad net must belong to an expected member
        extra = [p for p in have if p not in members and p.split(".")[0] not in members]
        if extra:
            errors.append(f"{ename} (KiCad net {knet}): unexpected pins {sorted(extra)}")
        if len(have) != want:
            errors.append(f"{ename} (KiCad net {knet}): {len(have)} pins, expected {want}")
    used = {p for ps in nets.values() for p in ps}
    print(f"KiCad nets: {len(nets)}, expected nets: {len(expect)}, pins connected: {len(used)}")
    if errors:
        print("MISMATCH:")
        for e in errors:
            print("  ", e)
        sys.exit(1)
    print("netlist matches the intended circuit")


if __name__ == "__main__":
    main()
