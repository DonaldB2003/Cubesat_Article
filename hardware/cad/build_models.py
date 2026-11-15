#!/usr/bin/env python3
"""Generate 3D models (GLB + STL) of the CubeSat, rescue tower and ground station.

    pip install trimesh manifold3d numpy
    python hardware/cad/build_models.py

Units: mm, Z up. Dimensions are taken from the project photos/diagrams where visible and
otherwise ASSUMED (marked "illustrative"). Edit the numbers and re-run.
Outputs:
  hardware/<device>/<device>.glb   coloured assembly (used by viewer/index.html)
  hardware/<device>/<device>.stl   single-colour assembly mesh
  hardware/<device>/parts.json     part names, groups and explode directions
  hardware/printable/*.stl         printable enclosures / spacers
"""
import json, pathlib
import numpy as np
import trimesh
from trimesh.creation import box as _box, cylinder as _cyl, icosphere

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GROUPS = {}   # filled per device


class Asm:
    """Collects named, coloured parts."""
    def __init__(self, name):
        self.name, self.parts = name, []      # (name, mesh, group, explode_dir, explode_dist)

    def add(self, name, mesh, color, group="body", ex=(0, 0, 1), dist=0.0):
        m = mesh.copy()
        m.visual.face_colors = np.tile(np.array(color, dtype=np.uint8), (len(m.faces), 1))
        self.parts.append((name, m, group, list(ex), float(dist)))
        return m

    def scene(self):
        s = trimesh.Scene()
        for name, m, *_ in self.parts:
            s.add_geometry(m, node_name=name, geom_name=name)
        return s

    def export(self, folder):
        folder = ROOT / folder; folder.mkdir(parents=True, exist_ok=True)
        self.scene().export(folder / f"{self.name}.glb")
        allm = trimesh.util.concatenate([m for _, m, *_ in self.parts])
        allm.export(folder / f"{self.name}.stl")
        meta = [dict(name=n, group=g, dir=d, dist=ds) for n, _, g, d, ds in self.parts]
        json.dump(meta, open(folder / "parts.json", "w"), indent=1)
        print(f"{self.name:15s} {len(self.parts):3d} parts  extents {np.round(allm.extents).astype(int)} mm")


def box(sx, sy, sz, c=(0, 0, 0)):
    m = _box(extents=[sx, sy, sz]); m.apply_translation(c); return m

def cyl(r, h, c=(0, 0, 0), axis="z", sec=40):
    m = _cyl(radius=r, height=h, sections=sec)
    if axis == "x": m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    if axis == "y": m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation(c); return m

def rod(p0, p1, r):
    return _cyl(radius=r, segment=[np.array(p0, float), np.array(p1, float)], sections=12)

def helix(radius, pitch, turns, wire_r, steps_per_turn=24):
    pts = [(radius * np.cos(t), radius * np.sin(t), pitch * t / (2 * np.pi))
           for t in np.linspace(0, 2 * np.pi * turns, int(steps_per_turn * turns) + 1)]
    return trimesh.util.concatenate([rod(a, b, wire_r) for a, b in zip(pts[:-1], pts[1:])])

def hollow_box(sx, sy, sz, wall):
    outer = box(sx, sy, sz, (0, 0, sz / 2))
    inner = box(sx - 2 * wall, sy - 2 * wall, sz, (0, 0, sz / 2 + wall))
    return outer.difference(inner, engine="manifold")

def place(m, R=None, t=(0, 0, 0)):
    m = m.copy()
    if R is not None: m.apply_transform(R)
    m.apply_translation(t); return m

def rot(angle_deg, axis):
    return trimesh.transformations.rotation_matrix(np.radians(angle_deg), axis)

PCB   = (24, 120, 60, 255)
PCB_B = (30, 90, 160, 255)
BLACK = (28, 30, 34, 255)
GRAY  = (150, 156, 162, 255)
GOLD  = (200, 160, 60, 255)
RED   = (210, 50, 45, 255)
GREEN = (60, 190, 90, 255)
BLUE  = (50, 110, 230, 255)
WHITE = (238, 240, 242, 255)
PINK  = (225, 90, 160, 255)
ORANGE= (230, 150, 40, 255)
SOLAR = (24, 40, 90, 255)
GLASS = (180, 205, 225, 70)


def antenna_with_dish(asm, base, tilt_deg, tag, helix_r=55, pitch=160, turns=3, dish_r=165, group="antenna", ex=(0, 0, 1)):
    """Axial-mode helix on a circular reflector; axis tilted about Y. Illustrative size."""
    R = rot(tilt_deg, [0, 1, 0])
    dish = cyl(dish_r, 3, (0, 0, 0), sec=64)
    h = helix(helix_r, pitch, turns, 2.5); h.apply_translation([0, 0, 3])
    boom = cyl(3, pitch * turns + 10, (0, 0, (pitch * turns + 10) / 2))
    asm.add(f"{tag}_reflector", place(dish, R, base), GRAY, group, ex, 120)
    asm.add(f"{tag}_helix", place(h, R, base), (210, 140, 60, 255), group, ex, 160)
    asm.add(f"{tag}_boom", place(boom, R, base), GRAY, group, ex, 140)


# =====================================================================
# CUBESAT  (100 x 100 x 100 mm stack of six boards on four corner rods)
# =====================================================================
def cubesat():
    a = Asm("cubesat")
    P = 45.0                     # rod offset from centre
    H = 100.0
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        a.add(f"frame_rod_{i+1}", cyl(1.6, H, (sx * P, sy * P, H / 2), sec=20), GRAY, "frame", (sx, sy, 0), 18)
    z = {"L6": 2.0, "L5": 26.0, "L4": 46.0, "L3": 64.0, "L2": 80.0, "L1": 96.0}
    ex = {"L6": 0, "L5": 20, "L4": 40, "L3": 60, "L2": 80, "L1": 100}
    names = {"L1": "Layer 1 Antenna", "L2": "Layer 2 Radio", "L3": "Layer 3 OBC",
             "L4": "Layer 4 Attitude + sensors", "L5": "Layer 5 Power + deploy", "L6": "Layer 6 Battery + magnet"}
    for L, zz in z.items():
        a.add(f"{L}_board", box(90, 90, 1.6, (0, 0, zz)), PCB, L, (0, 0, 1), ex[L])
    def on(L, name, m, color, dz=0):          # component sitting on a board top (m centred at origin)
        zt = z[L] + 0.8
        mm = m.copy(); mm.apply_translation([0, 0, zt - m.bounds[0][2]])
        a.add(f"{L}_{name}", mm, color, L, (0, 0, 1), ex[L] + dz)
    def at(m, x, y): m = m.copy(); m.apply_translation([x, y, 0]); return m
    # L1 antenna layer: dipole (two quarter-wave rods, 433 MHz ~173 mm each), GPS patch, SMA
    for s, nm in ((-1, "a"), (1, "b")):
        a.add(f"L1_dipole_{nm}", rod((s * 6, 0, z['L1'] + 7), (s * 179, 0, z['L1'] + 7), 2.4), WHITE, "L1", (s, 0, 0), 25)
    on("L1", "dipole_clamp", box(16, 12, 6), BLACK)
    on("L1", "gps_patch", at(box(25, 25, 4), 20, -22), (220, 190, 140, 255))
    on("L1", "sma", at(cyl(3, 9, (0, 0, 4.5)), -25, 28), GOLD)
    # L2 radio
    on("L2", "ra02_lora", at(box(17, 16, 3.5), -10, 5), PCB_B)
    on("L2", "ra02_shield", at(box(10, 10, 1.2, (0, 0, 2)), -10, 5), GRAY)
    on("L2", "pigtail_sma", at(cyl(3, 8, (0, 0, 4)), -30, 5), GOLD)
    # L3 on-board computer: Pi Zero W
    on("L3", "pi_zero_w", at(box(65, 30, 1.4, (0, 0, 0.7)), 0, 0), (30, 140, 70, 255))
    on("L3", "pi_cpu", at(box(12, 12, 1.4, (0, 0, 2.1)), 0, 0), BLACK)
    on("L3", "pi_hdr", at(box(51, 5, 8.5, (0, 0, 4.2)), 0, 11), BLACK)
    on("L3", "pi_sd", at(box(12, 15, 2, (0, 0, 1)), -26, 0), GRAY)
    # L4 attitude control + sensors
    on("L4", "mpu6050", at(box(21, 16, 3), -28, 30), PCB_B)
    on("L4", "bmp280", at(box(11, 15, 2.5), -6, 30), (120, 60, 160, 255))
    on("L4", "dht22", at(box(15, 25, 9), 20, 28), (225, 230, 235, 255))
    on("L4", "ds3231_rtc", at(box(23, 38, 5), 32, -10), PCB_B)
    a.add("L4_torque_rod_x", rod((-35, -26, z['L4'] + 4), (35, -26, z['L4'] + 4), 2.6), RED, "L4", (0, 0, 1), 40)
    a.add("L4_torque_rod_y", rod((-34, -38, z['L4'] + 4), (-34, 14, z['L4'] + 4), 2.6), RED, "L4", (0, 0, 1), 40)
    for nm, c, x in (("led_red", RED, -12), ("led_green", GREEN, 0), ("led_blue", BLUE, 12)):
        on("L4", nm, at(cyl(2.5, 5, (0, 0, 2.5)), x, 40), c)
    # L5 power + deploy
    on("L5", "boost_pmu", at(box(40, 25, 6), -20, 0), PCB_B)
    on("L5", "terminal_block", at(box(15, 10, 10), 12, 28), GREEN)
    on("L5", "mosfet_irfz44n", at(box(10, 4.5, 16, (0, 0, 8)), 28, 20), BLACK)
    on("L5", "mosfet_tab", at(box(10, 1.2, 8, (0, 0, 12)), 28, 17.6), GRAY)
    on("L5", "burnwire_post_a", at(cyl(1.8, 10, (0, 0, 5)), 26, -30), GOLD)
    on("L5", "burnwire_post_b", at(cyl(1.8, 10, (0, 0, 5)), 38, -30), GOLD)
    # L6 battery + magnet
    on("L6", "battery_holder", at(box(79, 22, 20, (0, 0, 10)), 0, 12), BLACK)
    on("L6", "cell_18650", at(cyl(9, 65, (0, 0, 14), axis="x"), 0, 12), PINK)
    on("L6", "magnet", at(box(40, 15, 8, (0, 0, 4)), 0, -30), (70, 70, 78, 255))
    # side solar panels (optional)
    for i, (nx, ny) in enumerate([(1, 0), (-1, 0), (0, 1), (0, -1)]):
        sz = (2, 90, 84) if nx else (90, 2, 84)
        a.add(f"solar_panel_{i+1}", box(*sz, (nx * 51, ny * 51, 50)), SOLAR, "solar", (nx, ny, 0), 30)
    a.add("frame_bottom_feet", box(96, 96, 1.0, (0, 0, -0.5)), GRAY, "frame", (0, 0, -1), 10)
    return a


# =====================================================================
# RESCUE TOWER (illustrative scale: 1.1 m mast)
# =====================================================================
def rescue_tower():
    a = Asm("rescue_tower")
    a.add("base_plate", box(320, 320, 12, (0, 0, 6)), (120, 126, 132, 255), "base", (0, 0, -1), 40)
    zs = np.linspace(12, 1100, 7)
    off = 65
    corners = [(-off, -off), (off, -off), (off, off), (-off, off)]
    for i, (x, y) in enumerate(corners):
        a.add(f"mast_leg_{i+1}", rod((x, y, 12), (x, y, 1100), 6), (170, 178, 186, 255), "mast", (0, 0, 1), 0)
    braces = []
    for k, zz in enumerate(zs):
        for i in range(4):
            p, q = corners[i], corners[(i + 1) % 4]
            braces.append(rod((*p, zz), (*q, zz), 3))
            if k < len(zs) - 1:
                braces.append(rod((*p, zz), (*q, zs[k + 1]), 2.4))
    a.add("mast_bracing", trimesh.util.concatenate(braces), (150, 158, 166, 255), "mast", (0, 0, 1), 0)
    # electronics enclosure on the +Y side of the mast (translucent)
    ex_, ey_, ez_ = 150, 90, 190
    ec = (0, off + ey_ / 2 + 8, 330)
    a.add("enc_enclosure", box(ex_, ey_, ez_, ec), GLASS, "enclosure", (0, 1, 0), 140)
    fy = ec[1] - ey_ / 2 + 4      # inside the back wall
    def inside(name, m, color, x, y_off, z, dist=100):
        mm = m.copy(); mm.apply_translation([x, ec[1] + y_off, z]); a.add(name, mm, color, "electronics", (0, 1, 0), dist)
    inside("esp32_devkit", box(55, 3, 28), (25, 40, 70, 255), -40, -10, 390)
    inside("esp32_module", box(18, 3.5, 25), GRAY, -26, -7, 390)
    inside("ra02_lora", box(17, 3.5, 16), PCB_B, 10, -10, 385)
    inside("neo6m_gps", box(36, 3.5, 27), PCB_B, 45, -10, 385)
    inside("gps_patch", box(25, 4, 25), (220, 190, 140, 255), 45, -6, 360)
    inside("pmu_board", box(60, 6, 40), PCB_B, -40, -10, 330, 70)
    inside("battery_18650", cyl(9, 65, axis="x"), PINK, 30, -10, 320, 70)
    # front face (+Y outer): OLED + SOS button
    front = ec[1] + ey_ / 2
    a.add("oled_display", box(32, 4, 20, (0, front + 2, 385)), (20, 40, 70, 255), "ui", (0, 1, 0), 180)
    a.add("oled_screen", box(26, 1, 14, (0, front + 4.5, 385)), (60, 190, 235, 255), "ui", (0, 1, 0), 180)
    a.add("sos_button_base", cyl(28, 8, (0, front + 4, 305), axis="y"), BLACK, "ui", (0, 1, 0), 180)
    a.add("sos_button", cyl(22, 12, (0, front + 12, 305), axis="y"), RED, "ui", (0, 1, 0), 200)
    # beacon + antenna on top
    a.add("beacon_base", cyl(32, 16, (0, 0, 1108)), BLACK, "beacon", (0, 0, 1), 120)
    a.add("beacon_lamp", cyl(28, 45, (0, 0, 1138)), (230, 40, 40, 190), "beacon", (0, 0, 1), 150)
    a.add("beacon_cap", cyl(18, 8, (0, 0, 1164)), BLACK, "beacon", (0, 0, 1), 160)
    antenna_with_dish(a, (0, 0, 1200), 40, "rtt_antenna", group="antenna", ex=(1, 0, 1))
    a.add("antenna_mast", rod((0, 0, 1100), (0, 0, 1200), 8), (170, 178, 186, 255), "antenna", (0, 0, 1), 90)
    # solar panel on a bracket (-X side)
    sp = box(260, 8, 330); sp.apply_transform(rot(35, [0, 1, 0])); sp.apply_translation([-200, 0, 780])
    a.add("solar_panel", sp, SOLAR, "solar", (-1, 0, 0), 150)
    a.add("solar_bracket", rod((-off, 0, 700), (-155, 0, 700), 4), GRAY, "solar", (-1, 0, 0), 150)
    return a


# =====================================================================
# GROUND STATION (enclosure + antenna mast)
# =====================================================================
def ground_station():
    a = Asm("ground_station")
    W, D, Hh, wall = 170, 110, 55, 3
    a.add("table_plate", box(420, 260, 10, (60, 0, -5)), (150, 120, 85, 255), "base", (0, 0, -1), 40)
    a.add("enc_base", place(hollow_box(W, D, Hh, wall), None, (0, 0, 0)), (60, 66, 74, 255), "enclosure", (0, 0, 1), 0)
    a.add("enc_lid", box(W, D, 3, (0, 0, Hh + 1.5)), (60, 66, 74, 150), "enclosure", (0, 0, 1), 90)
    zf = wall + 1
    a.add("perfboard", box(150, 90, 1.6, (0, 0, zf + 4)), PCB, "electronics", (0, 0, 1), 20)
    zt = zf + 4.8
    def top(name, sx, sy, sz, x, y, color, dist=40):
        a.add(name, box(sx, sy, sz, (x, y, zt + sz / 2)), color, "electronics", (0, 0, 1), dist)
    top("arduino_nano", 45, 18, 6, -45, 20, (20, 90, 150, 255))
    top("nano_usb", 8, 8, 4, -66, 20, GRAY, 45)
    top("esp32_devkit", 51, 28, 6, 30, 22, (25, 40, 70, 255))
    top("esp32_module", 18, 25, 3, 42, 22, GRAY, 50)
    top("ra02_lora", 17, 16, 3.5, -30, -20, PCB_B)
    top("level_shift_resistors", 22, 8, 3, -5, -5, (200, 170, 100, 255))
    top("status_led_green", 5, 5, 5, 55, -25, GREEN, 60)
    top("status_led_red", 5, 5, 5, 65, -25, RED, 60)
    top("buzzer", 12, 12, 9, 40, -25, BLACK, 60)
    # SMA bulkhead + USB cable stub on +X wall
    a.add("sma_bulkhead", cyl(4, 14, (W / 2 + 4, -20, 25), axis="x"), GOLD, "electronics", (1, 0, 0), 60)
    a.add("usb_cable_stub", box(14, 10, 6, (W / 2 + 7, 22, 20)), BLACK, "electronics", (1, 0, 0), 60)
    # mast + antenna
    a.add("mast_pole", cyl(11, 650, (170, 0, 325)), (180, 184, 190, 255), "antenna", (0, 0, 1), 0)
    a.add("mast_foot", cyl(60, 10, (170, 0, 5)), GRAY, "antenna", (0, 0, -1), 20)
    antenna_with_dish(a, (170, 0, 650), 35, "rcs_antenna", group="antenna", ex=(0, 0, 1))
    a.add("coax_run", rod((W / 2 + 12, -20, 25), (170, 0, 70), 2.4), BLACK, "antenna", (0, 0, 1), 0)
    return a


# =====================================================================
# PRINTABLE PARTS
# =====================================================================
def printable():
    out = ROOT / "hardware" / "printable"; out.mkdir(parents=True, exist_ok=True)
    def save(name, m):
        m.export(out / f"{name}.stl")
        print(f"  {name:32s} watertight={m.is_watertight!s:5s} {np.round(m.extents,1)} mm")
    # CubeSat spacers (tube) and antenna clamp
    sp = cyl(3.5, 18, (0, 0, 9), sec=48).difference(cyl(1.7, 20, (0, 0, 9), sec=32), engine="manifold")
    save("cubesat_board_spacer_18mm", sp)
    cl = box(16, 12, 8, (0, 0, 4)).difference(cyl(2.6, 20, (0, 0, 6), axis="y", sec=32), engine="manifold")
    cl = cl.difference(cyl(1.6, 20, (0, 0, 4), axis="z", sec=24), engine="manifold")
    save("cubesat_dipole_clamp", cl)
    # Ground station enclosure
    W, D, Hh, wall = 170, 110, 55, 3
    base = hollow_box(W, D, Hh, wall)
    for x in (-1, 1):                         # four screw posts
        for y in (-1, 1):
            post = cyl(4, Hh - wall, (x * (W / 2 - 8), y * (D / 2 - 8), wall + (Hh - wall) / 2), sec=32)
            hole = cyl(1.4, Hh - wall, (x * (W / 2 - 8), y * (D / 2 - 8), wall + (Hh - wall) / 2 + 2), sec=24)
            base = base.union(post, engine="manifold").difference(hole, engine="manifold")
    base = base.difference(cyl(4.3, 12, (W / 2, -20, 25), axis="x", sec=32), engine="manifold")     # SMA
    base = base.difference(box(12, 12, 8, (W / 2, 22, 20)), engine="manifold")                      # USB
    base = base.difference(box(10, 10, 6, (-W / 2, 20, 20)), engine="manifold")                     # Nano USB
    save("ground_station_enclosure_base", base)
    lid = box(W, D, 3, (0, 0, 1.5))
    for x in (-1, 1):
        for y in (-1, 1):
            lid = lid.difference(cyl(1.8, 6, (x * (W / 2 - 8), y * (D / 2 - 8), 1.5), sec=24), engine="manifold")
    for x in (55, 65):
        lid = lid.difference(cyl(2.6, 6, (x, -25, 1.5), sec=24), engine="manifold")                 # LED holes
    save("ground_station_enclosure_lid", lid)
    # Rescue tower enclosure (150 x 90 x 190)
    ex_, ey_, ez_, w = 150, 90, 190, 3
    tb = hollow_box(ex_, ey_, ez_, w).difference(box(ex_ - 2 * w, ey_ - 2 * w, 8, (0, 0, ez_ - 4)), engine="manifold")
    tb = tb.difference(box(28, w + 2, 18, (0, ey_ / 2, 150)), engine="manifold")      # OLED window (front +Y)
    tb = tb.difference(cyl(15, w + 2, (0, ey_ / 2, 70), axis="y", sec=48), engine="manifold")  # SOS button hole
    tb = tb.difference(cyl(4.3, 12, (ex_ / 2, 0, 30), axis="x", sec=32), engine="manifold")               # SMA
    tb = tb.difference(box(12, 12, 8, (-ex_ / 2, 0, 30)), engine="manifold")                              # solar cable
    save("rescue_tower_enclosure_base", tb)
    tl = box(ex_, ey_, 3, (0, 0, 1.5))
    for x in (-1, 1):
        for y in (-1, 1):
            tl = tl.difference(cyl(1.8, 6, (x * (ex_ / 2 - 8), y * (ey_ / 2 - 8), 1.5), sec=24), engine="manifold")
    save("rescue_tower_enclosure_lid", tl)


if __name__ == "__main__":
    print("Assemblies")
    cubesat().export("hardware/cubesat")
    rescue_tower().export("hardware/rescue_tower")
    ground_station().export("hardware/ground_station")
    print("Printable parts")
    printable()
