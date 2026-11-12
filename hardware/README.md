# Hardware

KiCad 10 projects, fabricated and assembled at JLCPCB.

| Folder | Board | Layers | Contents |
|---|---|---|---|
| `main-board/` | Main board | 4 | Power, analog input, bypass relay, outputs, headphone amp, Daisy Seed (bottom side) |
| `control-board/` | Control board | 2 | 40 pots + 5× 74HC4051, buttons, encoder, LEDs + LED driver |
| `front-panel/` | Front panel | 2 | Cosmetic PCB: graphics, holes, LED diffusion windows |

Symbols, footprints and 3D models come from the personal global JLCPCB library
(`~/Documents/KiCad/JLCPCB-Library/`, path variable `JLCPCB_LIB`).
See `../CLAUDE.md` for the hardware rules.
