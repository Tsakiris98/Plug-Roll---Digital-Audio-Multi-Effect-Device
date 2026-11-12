"""Minimal KiCad 10 schematic writer used to build the Plug & Roll sheets.

It places library symbols on a grid, computes the absolute position of every
pin, and writes wires, labels, junctions and power symbols. Symbol definitions
are copied from the real libraries (the personal JLCPCB library and KiCad's
stock libraries), so the schematic embeds exactly what the libraries contain.

All coordinates are millimetres, y grows downwards (as on the KiCad screen).
"""
import math
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
STOCK = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
JLC_LIB = Path.home() / "Documents/KiCad/JLCPCB-Library/JLCPCB.kicad_sym"
NS = uuid.UUID("6f0a1c1e-7d2b-4a55-9f3e-0c5d2b7a9e11")


def uid(*parts):
    """Stable UUID, so regenerating a sheet does not change every id."""
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _block(t, i):
    d = 0
    for j in range(i, len(t)):
        if t[j] == "(":
            d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0:
                return t[i:j + 1]
    raise ValueError("unbalanced")


def _fmt(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


class Libraries:
    """Loads symbol definitions in KiCad 10 format."""

    def __init__(self):
        self._text = {}

    def _lib(self, lib):
        if lib not in self._text:
            if lib == "JLCPCB":
                # The personal library is kept in the format easyeda2kicad
                # writes. Upgrade a temporary copy to the current format.
                tmp = Path(tempfile.mkdtemp()) / "JLCPCB.kicad_sym"
                tmp.write_text(JLC_LIB.read_text())
                subprocess.run([KICAD_CLI, "sym", "upgrade", str(tmp)],
                               check=True, capture_output=True)
                self._text[lib] = tmp.read_text()
            else:
                self._text[lib] = (STOCK / f"{lib}.kicad_sym").read_text()
        return self._text[lib]

    def _raw(self, lib, name):
        t = self._lib(lib)
        m = re.search(r'\n\t\(symbol %s\n' % re.escape(q(name)), t)
        if not m:
            raise KeyError(f"{lib}:{name} not found")
        return _block(t, m.start() + 2)

    def symbol(self, lib_id):
        lib, name = lib_id.split(":", 1)
        b = self._raw(lib, name)
        ext = re.search(r'\(extends "([^"]+)"\)', b)
        if ext:
            # Derived symbol: graphics and pins of the parent, fields of the child.
            parent = self._raw(lib, ext.group(1))
            pname = ext.group(1)
            body = parent.replace(f'(symbol {q(pname)}', f'(symbol {q(name)}', 1)
            body = body.replace(f'(symbol "{pname}_', f'(symbol "{name}_')
            # Fields: the parent's, each replaced by the child's where the child defines it.
            child = {}
            for m in re.finditer(r'\n\t\t\(property "([^"]+)"', b):
                child[m.group(1)] = _block(b, m.start() + 3)
            for m in reversed(list(re.finditer(r'\n\t\t\(property "([^"]+)"', body))):
                pb = _block(body, m.start() + 3)
                if m.group(1) in child:
                    body = body[:m.start() + 3] + child.pop(m.group(1)) + body[m.start() + 3 + len(pb):]
            # Fields only the child has go after the last field.
            last = list(re.finditer(r'\n\t\t\(property "([^"]+)"', body))[-1]
            end = last.start() + 3 + len(_block(body, last.start() + 3))
            body = body[:end] + "".join("\n\t\t" + v for v in child.values()) + body[end:]
            b = body
        return LibSymbol(lib_id, name, b)


class LibSymbol:
    def __init__(self, lib_id, name, body):
        self.lib_id, self.name, self.body = lib_id, name, body
        self.pins = []  # (unit, number, name, x, y)
        for m in re.finditer(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(name), body):
            sb = _block(body, m.start())
            for p in re.finditer(r'\(pin \w+ \w+', sb):
                pb = _block(sb, p.start())
                at = re.search(r'\(at ([-\d.]+) ([-\d.]+)', pb)
                self.pins.append((int(m.group(1)),
                                  re.search(r'\(number "([^"]*)"', pb).group(1),
                                  re.search(r'\(name "([^"]*)"', pb).group(1),
                                  float(at.group(1)), float(at.group(2))))
        self.props = {}
        for m in re.finditer(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)"', body):
            self.props.setdefault(m.group(1), m.group(2))

    def embedded(self):
        return self.body.replace(f'(symbol {q(self.name)}', f'(symbol {q(self.lib_id)}', 1)


class Inst:
    def __init__(self, sheet, sym, ref, value, at, rot, mirror, unit, fields):
        self.sheet, self.sym, self.ref, self.value = sheet, sym, ref, value
        self.x, self.y = round(at[0], 2), round(at[1], 2)
        self.rot, self.mirror, self.unit, self.fields = rot, mirror, unit, fields

    def _xf(self, px, py):
        x, y = px, -py
        if self.mirror == "x":
            y = -y
        elif self.mirror == "y":
            x = -x
        a = math.radians(self.rot)
        xr = x * math.cos(a) + y * math.sin(a)
        yr = -x * math.sin(a) + y * math.cos(a)
        return (round(self.x + xr, 2), round(self.y + yr, 2))

    def pin(self, number):
        for u, n, name, px, py in self.sym.pins:
            if n == str(number) and (u in (0, self.unit)):
                return self._xf(px, py)
        raise KeyError(f"{self.ref} has no pin {number} in unit {self.unit}")

    def unit_pins(self):
        return [(n, self._xf(px, py)) for u, n, name, px, py in self.sym.pins if u in (0, self.unit)]

    def _extreme(self, key):
        return sorted(self.unit_pins(), key=key)[0][1]

    left = property(lambda s: s._extreme(lambda p: p[1][0]))
    right = property(lambda s: s._extreme(lambda p: -p[1][0]))
    top = property(lambda s: s._extreme(lambda p: p[1][1]))
    bottom = property(lambda s: s._extreme(lambda p: -p[1][1]))


class Sheet:
    def __init__(self, libs, project, path, paper="A3", title="", rev="", file_uuid=None, pwr_base=0):
        self.libs, self.project, self.path = libs, project, path
        self.paper, self.title, self.rev = paper, title, rev
        self.file_uuid = file_uuid
        self.items, self.used, self.insts = [], {}, []
        self._pwr = pwr_base      # power symbol references must be unique in the whole project
        self._n = 0

    def _id(self, kind):
        self._n += 1
        return uid(self.path, kind, self._n)

    # ---- symbols -------------------------------------------------------
    def add(self, lib_id, ref, value, at, rot=0, mirror=None, unit=1, fields=None,
            ref_at=None, val_at=None):
        sym = self.used.get(lib_id) or self.libs.symbol(lib_id)
        self.used[lib_id] = sym
        inst = Inst(self, sym, ref, value, at, rot, mirror, unit, fields or {})
        inst.ref_at, inst.val_at = ref_at, val_at
        self.insts.append(inst)
        return inst

    def power(self, name, at, rot=0):
        self._pwr += 1
        return self.add(f"power:{name}", f"#PWR{self._pwr:03d}", name, at, rot)

    # ---- wiring --------------------------------------------------------
    def wire(self, *pts):
        pts = [(round(p[0], 2), round(p[1], 2)) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            assert a[0] == b[0] or a[1] == b[1], f"diagonal wire {a} {b}"
            self.items.append(
                f'\t(wire\n\t\t(pts\n\t\t\t(xy {_fmt(a[0])} {_fmt(a[1])}) (xy {_fmt(b[0])} {_fmt(b[1])})\n\t\t)\n'
                f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid {q(self._id("wire"))})\n\t)')

    def junction(self, at):
        self.items.append(f'\t(junction\n\t\t(at {_fmt(at[0])} {_fmt(at[1])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n'
                          f'\t\t(uuid {q(self._id("junction"))})\n\t)')

    def no_connect(self, at):
        self.items.append(f'\t(no_connect\n\t\t(at {_fmt(at[0])} {_fmt(at[1])})\n\t\t(uuid {q(self._id("nc"))})\n\t)')

    def label(self, name, at, rot=0):
        just = "left bottom" if rot in (0, 90) else "right bottom"
        self.items.append(f'\t(label {q(name)}\n\t\t(at {_fmt(at[0])} {_fmt(at[1])} {rot})\n\t\t(effects\n\t\t\t(font\n'
                          f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid {q(self._id("label"))})\n\t)')

    def glabel(self, name, at, rot=0):
        """Global label: connects to the same name on every sheet."""
        just = "left" if rot in (0, 90) else "right"
        self.items.append(
            f'\t(global_label {q(name)}\n\t\t(shape passive)\n\t\t(at {_fmt(at[0])} {_fmt(at[1])} {rot})\n\t\t(effects\n\t\t\t(font\n'
            f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid {q(self._id("glabel"))})\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {_fmt(at[0])} {_fmt(at[1])} 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify {just})\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n\t)')

    def text(self, s, at, size=1.27):
        self.items.append(f'\t(text {q(s)}\n\t\t(exclude_from_sim no)\n\t\t(at {_fmt(at[0])} {_fmt(at[1])} 0)\n\t\t(effects\n'
                          f'\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n'
                          f'\t\t(uuid {q(self._id("text"))})\n\t)')

    def subsheet(self, name, filename, at, size, page):
        su = uid(self.path, "sheet", name)
        self.items.append(
            f'\t(sheet\n\t\t(at {_fmt(at[0])} {_fmt(at[1])})\n\t\t(size {_fmt(size[0])} {_fmt(size[1])})\n'
            f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
            f'\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n'
            f'\t\t(uuid {q(su)})\n'
            f'\t\t(property "Sheetname" {q(name)}\n\t\t\t(at {_fmt(at[0])} {_fmt(at[1] - 0.7)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
            f'\t\t(property "Sheetfile" {q(filename)}\n\t\t\t(at {_fmt(at[0])} {_fmt(at[1] + size[1] + 0.6)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project {q(self.project)}\n\t\t\t\t(path {q(self.path)}\n\t\t\t\t\t(page {q(page)})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        return su

    # ---- output --------------------------------------------------------
    def _prop(self, name, value, at, angle, hide):
        h = "\n\t\t\t(hide yes)" if hide else ""
        return (f'\t\t(property {q(name)} {q(value)}\n\t\t\t(at {_fmt(at[0])} {_fmt(at[1])} {angle}){h}\n\t\t\t(effects\n'
                f'\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)')

    def _symbol(self, i):
        s = i.sym
        vertical = i.rot in (90, 270)
        ang = 90 if vertical else 0
        if i.ref_at is None:
            i.ref_at = (i.x + 6.35, i.y - 1.27) if vertical else (i.x, i.y - 3.81)
        if i.val_at is None:
            i.val_at = (i.x + 6.35, i.y + 1.27) if vertical else (i.x, i.y + 3.81)
        power = s.lib_id.startswith("power:")
        out = [f'\t(symbol\n\t\t(lib_id {q(s.lib_id)})\n\t\t(at {_fmt(i.x)} {_fmt(i.y)} {i.rot})']
        if i.mirror:
            out.append(f'\t\t(mirror {i.mirror})')
        out.append(f'\t\t(unit {i.unit})\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
                   f'\t\t(uuid {q(uid(self.path, "sym", i.ref, i.unit))})')
        out.append(self._prop("Reference", i.ref, i.ref_at, ang, power))
        if power:
            below = i.value.startswith("GND") or i.rot == 180
            out.append(self._prop("Value", i.value, (i.x, i.y + 5.08 if below else i.y - 3.81), 0, False))
        else:
            out.append(self._prop("Value", i.value, i.val_at, ang, False))
        props = dict(s.props)
        props.update(i.fields)
        for k in ("Footprint", "Datasheet", "Description"):
            out.append(self._prop(k, props.get(k, ""), (i.x, i.y), 0, True))
        for k, v in props.items():
            if k in ("Reference", "Value", "Footprint", "Datasheet", "Description") or k.startswith("ki_"):
                continue
            out.append(self._prop(k, v, (i.x, i.y), 0, True))
        for n in sorted({n for u, n, *_ in s.pins if u in (0, i.unit)}):
            out.append(f'\t\t(pin {q(n)}\n\t\t\t(uuid {q(uid(self.path, "pin", i.ref, i.unit, n))})\n\t\t)')
        out.append(f'\t\t(instances\n\t\t\t(project {q(self.project)}\n\t\t\t\t(path {q(self.path)}\n'
                   f'\t\t\t\t\t(reference {q(i.ref)})\n\t\t\t\t\t(unit {i.unit})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)')
        return "\n".join(out)

    def render(self, root_page=None):
        libsyms = "\n".join("\t\t" + s.embedded().replace("\n", "\n\t") for s in self.used.values())
        head = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
                f'\t(uuid {q(self.file_uuid)})\n\t(paper {q(self.paper)})\n'
                f'\t(title_block\n\t\t(title {q(self.title)})\n\t\t(rev {q(self.rev)})\n\t)\n'
                f'\t(lib_symbols\n{libsyms}\n\t)')
        body = "\n".join(self.items + [self._symbol(i) for i in self.insts])
        tail = ""
        if root_page:
            tail = f'\n\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page {q(root_page)})\n\t\t)\n\t)'
        return head + "\n" + body + tail + "\n\t(embedded_fonts no)\n)\n"
