#!/usr/bin/env python3
"""Generate circuit diagrams (SVG) and pin-map CSVs for the three devices.

Style: module boxes with net-label tags (the same label on two pins = connected).
    python hardware/cad/schematics.py
CubeSat pins come from the project README. Rescue tower and ground station pins are
PROPOSED (not documented in the README): check them against your build and edit below.
"""
import csv, pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
ROW, STUB = 22, 22

NETCOL = {"3V3": "#c2410c", "5V": "#b91c1c", "VBAT": "#b91c1c", "GND": "#475569", "SOLAR": "#a16207",
          "MOSI": "#2563eb", "MISO": "#2563eb", "SCK": "#2563eb", "NSS": "#2563eb", "RST": "#2563eb", "DIO0": "#2563eb",
          "SDA": "#15803d", "SCL": "#15803d",
          "GPS_TX": "#7c3aed", "GPS_RX": "#7c3aed", "TX": "#7c3aed", "RX": "#7c3aed",
          "BURN": "#be123c", "DHT": "#0f766e", "SOS": "#be123c", "BEACON": "#be123c", "BUZ": "#0f766e",
          "LED_R": "#dc2626", "LED_G": "#16a34a", "LED_B": "#2563eb", "AD0": "#c2410c"}
def col(net):
    base = net.replace("(5V)", "").replace("_5V", "")
    return NETCOL.get(net, NETCOL.get(base, "#334155"))

STYLE = """text{font-family:Helvetica,Arial,sans-serif;fill:#0f172a}
.blk{fill:#fff;stroke:#64748b;stroke-width:1.5}.ttl{font-size:15px;font-weight:700}
.sub{font-size:11px;fill:#64748b;font-family:Menlo,Consolas,monospace}.pn{font-size:12px;font-family:Menlo,Consolas,monospace}
.net{font-size:12px;font-weight:700;font-family:Menlo,Consolas,monospace}.h1{font-size:22px;font-weight:700}
.note{font-size:12px;fill:#475569}.sym{fill:none;stroke:#334155;stroke-width:1.8}.wire{fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}"""


class Sheet:
    def __init__(self, w, h, title, subtitle=""):
        self.w, self.h, self.o = w, h, []
        self.t(24, 36, title, "h1")
        if subtitle: self.t(24, 56, subtitle, "note")
        self.pins = []        # (module, pin, net, gpio_text)

    def t(self, x, y, s, cls="", anchor="start", fill=None):
        f = f' fill="{fill}"' if fill else ""
        self.o.append(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{f}>{escape(str(s))}</text>')

    def module(self, x, y, w, title, sub="", left=(), right=(), color="#fff", note=None):
        n = max(len(left), len(right), 1); h = 56 + n * ROW + 10
        self.o.append(f'<rect class="blk" x="{x}" y="{y}" width="{w}" height="{h}" rx="7" style="fill:{color}"/>')
        self.t(x + 12, y + 24, title, "ttl")
        if sub: self.t(x + 12, y + 41, sub, "sub")
        for side, pins in (("L", left), ("R", right)):
            for i, (pin, net) in enumerate(pins):
                py = y + 62 + i * ROW
                px = x if side == "L" else x + w
                d = -1 if side == "L" else 1
                c = col(net) if net else "#64748b"
                self.o.append(f'<circle cx="{px}" cy="{py}" r="3" fill="#64748b"/>')
                self.t(px - d * 9, py + 4, pin, "pn", "start" if side == "L" else "end")
                if net:
                    ex = px + d * STUB
                    self.o.append(f'<line class="wire" x1="{px}" y1="{py}" x2="{ex}" y2="{py}" stroke="{c}"/>')
                    self.o.append(f'<circle cx="{ex}" cy="{py}" r="3.4" fill="{c}"/>')
                    self.t(ex + d * 7, py + 4, net, "net", "end" if side == "L" else "start", c)
                    self.pins.append((title, pin, net))
        if note: self.t(x + 2, y + h + 16, note, "note")
        return h

    def raw(self, s): self.o.append(s)

    def save(self, path, legend=True):
        body = "".join(self.o)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}">'
               f'<style>{STYLE}</style><rect width="100%" height="100%" fill="#f8fafc"/>{body}</svg>')
        pathlib.Path(path).write_text(svg)

    def pinmap(self, path):
        with open(path, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["module", "pin", "net"]); w.writerows(self.pins)


def cubesat():
    s = Sheet(1480, 940, "CubeSat circuit", "Raspberry Pi Zero W flight computer. Pins from the project README. Same net label = connected.")
    # left stack
    y = 80
    h = s.module(60, y, 250, "LoRa RA-02", "433 MHz SPI radio", right=[("RST", "RST"), ("NSS", "NSS"), ("DIO0", "DIO0"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("SCK", "SCK"), ("3V3", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(60, y, 250, "BMP280", "I2C 0x76", right=[("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(60, y, 250, "MPU-6050", "I2C 0x69 (AD0 high)", right=[("SDA", "SDA"), ("SCL", "SCL"), ("AD0", "3V3"), ("VCC", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(60, y, 250, "DS3231 RTC", "I2C 0x68", right=[("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")])
    # Pi
    s.module(560, 80, 360, "Raspberry Pi Zero W", "on-board computer (layer 3)",
             left=[("GPIO17", "RST"), ("GPIO8 CE0", "NSS"), ("GPIO4", "DIO0"), ("GPIO10 MOSI", "MOSI"), ("GPIO9 MISO", "MISO"),
                   ("GPIO11 SCLK", "SCK"), ("GPIO2 SDA", "SDA"), ("GPIO3 SCL", "SCL"), ("3V3", "3V3"), ("GND", "GND")],
             right=[("GPIO14 TXD", "GPS_RX"), ("GPIO15 RXD", "GPS_TX"), ("GPIO24", "DHT"), ("GPIO18", "BURN"),
                    ("GPIO23", "LED_R"), ("GPIO25", "LED_G"), ("GPIO16", "LED_B"), ("5V", "5V"), ("GND", "GND")], color="#ecfdf5")
    # right stack
    y = 80
    h = s.module(1170, y, 250, "NEO-6M GPS", "UART 9600", left=[("TX", "GPS_TX"), ("RX", "GPS_RX"), ("VCC", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(1170, y, 250, "DHT22", "temperature + humidity", left=[("DATA", "DHT"), ("VCC", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(1170, y, 250, "Status LEDs", "330 ohm in series with each", left=[("RED anode", "LED_R"), ("GREEN anode", "LED_G"), ("BLUE anode", "LED_B"), ("cathodes", "GND")]); y += h + 22
    h = s.module(1170, y, 250, "Burn-wire driver", "N-MOSFET + nichrome, see sheet 2", left=[("GATE input", "BURN"), ("VBAT", "VBAT"), ("GND", "GND")]); y += h + 22
    s.module(1170, y, 250, "Power: 18650 + boost", "layer 5/6", left=[("5V out", "5V"), ("BAT+ rail", "VBAT"), ("GND", "GND")])
    s.t(560, 460, "Red = power on, green = 1 Hz heartbeat, blue = TX blink", "note")
    s.t(560, 482, "MPU-6050 AD0 high moves it to 0x69 so it does not clash with the DS3231 at 0x68.", "note")
    s.save(ROOT / "cubesat" / "circuit.svg"); s.pinmap(ROOT / "cubesat" / "pinmap.csv")


def burnwire():
    s = Sheet(1000, 620, "CubeSat antenna-deploy burn-wire driver", "Redrawn from the original sketch. Nichrome heats when GPIO18 turns the MOSFET on.")
    c = "#334155"
    def line(*pts, colr=c): s.raw(f'<polyline class="wire" points="{" ".join(f"{a},{b}" for a, b in pts)}" stroke="{colr}"/>')
    def res(x1, y1, x2, y2):
        if y1 == y2:
            m = (x1 + x2) / 2
            s.raw(f'<path class="sym" d="M{x1} {y1}H{m-30}l5 -10 10 20 10 -20 10 20 10 -20 5 10H{x2}"/>')
        else:
            m = (y1 + y2) / 2
            s.raw(f'<path class="sym" d="M{x1} {y1}V{m-30}l-10 5 20 10 -20 10 20 10 -20 10 10 5V{y2}"/>')
    def gnd(x, y):
        s.raw(f'<path class="sym" d="M{x} {y}V{y+10}M{x-14} {y+10}H{x+14}M{x-9} {y+16}H{x+9}M{x-4} {y+22}H{x+4}"/>')
    s.module(60, 270, 150, "Raspberry Pi", "GPIO18", right=[("GPIO18", None)])
    line((210, 332), (330, 332)); res(330, 332, 450, 332); line((450, 332), (560, 332))
    s.t(390, 316, "R1 1 k", "pn", "middle")
    s.raw('<circle cx="500" cy="332" r="3.6" fill="#334155"/>'); line((500, 332), (500, 360)); res(500, 360, 500, 470); line((500, 470), (500, 500)); gnd(500, 500)
    s.t(515, 420, "R2 10 k", "pn"); s.t(515, 436, "gate pull-down", "note")
    # MOSFET
    s.raw('<circle cx="640" cy="332" r="70" fill="none" stroke="#94a3b8" stroke-width="1.4"/>')
    line((560, 332), (610, 332)); line((610, 300), (610, 364))
    line((622, 296), (622, 312)); line((622, 324), (622, 340)); line((622, 352), (622, 368))
    line((622, 304), (680, 304), (680, 250)); line((622, 360), (680, 360), (680, 420))
    line((622, 332), (660, 332))
    s.raw('<polygon points="622,332 640,324 640,340" fill="#334155"/>')
    s.t(700, 270, "Drain", "pn"); s.t(700, 405, "Source", "pn"); s.t(560, 322, "Gate", "pn", "end")
    s.t(720, 470, "IRFZ44N N-MOSFET (body diode is inside the package)", "note")
    line((680, 420), (680, 520)); gnd(680, 520); line((500, 500), (680, 500))
    # nichrome + supply
    line((680, 250), (680, 190)); res(680, 190, 680, 100); line((680, 100), (680, 70))
    s.t(700, 150, "Nichrome wire (burn wire)", "pn")
    s.raw('<line class="wire" x1="600" y1="70" x2="760" y2="70" stroke="#b91c1c"/>'); s.t(770, 74, "VBAT +3.7 V", "net", "start", "#b91c1c")
    s.t(60, 560, "Gate resistor limits GPIO current; the pull-down keeps the wire off while the Pi boots.", "note")
    s.t(60, 580, "Note: the IRFZ44N is a standard-gate MOSFET. At 3.3 V drive it may not turn fully on; an IRLZ44N (logic level) is a safer choice.", "note")
    s.save(ROOT / "cubesat" / "burnwire.svg")


def tower():
    s = Sheet(1480, 780, "Rescue tower circuit (PROPOSED pins)", "ESP32 + LoRa RA-02 + OLED + GPS + SOS button + beacon, solar powered. Pins are a proposal: edit hardware/cad/schematics.py to match your wiring.")
    y = 90
    h = s.module(60, y, 250, "LoRa RA-02", "433 MHz SPI radio", right=[("RST", "RST"), ("NSS", "NSS"), ("DIO0", "DIO0"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("SCK", "SCK"), ("3V3", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(60, y, 250, "OLED SSD1306", "I2C 0x3C, SOS acknowledge + info", right=[("SDA", "SDA"), ("SCL", "SCL"), ("VCC", "3V3"), ("GND", "GND")]); y += h + 22
    h = s.module(60, y, 250, "NEO-6M GPS", "UART 9600", right=[("TX", "GPS_TX"), ("RX", "GPS_RX"), ("VCC", "3V3"), ("GND", "GND")])
    s.module(560, 90, 360, "ESP32 DevKit", "master controller",
             left=[("GPIO5", "NSS"), ("GPIO14", "RST"), ("GPIO26", "DIO0"), ("GPIO23 MOSI", "MOSI"), ("GPIO19 MISO", "MISO"), ("GPIO18 SCK", "SCK"),
                   ("GPIO21 SDA", "SDA"), ("GPIO22 SCL", "SCL"), ("GPIO16 RX2", "GPS_TX"), ("GPIO17 TX2", "GPS_RX"), ("3V3", "3V3"), ("GND", "GND")],
             right=[("GPIO27", "SOS"), ("GPIO25", "BEACON"), ("GPIO33", "BUZ"), ("VIN 5V", "5V"), ("GND", "GND")], color="#eff6ff")
    y = 90
    h = s.module(1170, y, 250, "SOS push button", "to GND, internal pull-up", left=[("one side", "SOS"), ("other side", "GND")]); y += h + 22
    h = s.module(1170, y, 250, "Beacon driver", "1 k + 2N2222 + beacon LED/lamp", left=[("base via 1 k", "BEACON"), ("supply", "5V"), ("emitter", "GND")]); y += h + 22
    h = s.module(1170, y, 250, "Buzzer (optional)", "active 5 V buzzer", left=[("+", "BUZ"), ("-", "GND")]); y += h + 22
    s.module(1170, y, 250, "Power chain", "solar panel > solar PMU > 18650 > 5 V", left=[("5V out", "5V"), ("GND", "GND")])
    s.t(560, 480, "Keep RA-02 on the 3V3 rail with a 10 uF + 100 nF decoupling pair.", "note")
    s.t(560, 502, "Solar panel and 18650 connect to the PMU board. The ESP32 3V3 regulator feeds RA-02, OLED and GPS.", "note")
    s.save(ROOT / "rescue_tower" / "circuit.svg"); s.pinmap(ROOT / "rescue_tower" / "pinmap.csv")


def ground():
    s = Sheet(1560, 700, "Ground station circuit (PROPOSED pins)", "Arduino Nano decodes LoRa, ESP32 handles WiFi / internet. Pins are a proposal: edit hardware/cad/schematics.py to match your wiring.")
    s.module(40, 100, 230, "LoRa RA-02", "3.3 V only", right=[("RST", "RST"), ("NSS", "NSS"), ("DIO0", "DIO0"), ("MOSI", "MOSI"), ("MISO", "MISO"), ("SCK", "SCK"), ("3V3", "3V3"), ("GND", "GND")])
    s.module(430, 100, 260, "Level divider 4x", "1 k series / 2 k to GND", left=[("NSS out", "NSS"), ("RST out", "RST"), ("MOSI out", "MOSI"), ("SCK out", "SCK")],
             right=[("NSS in 5V", "NSS(5V)"), ("RST in 5V", "RST(5V)"), ("MOSI in 5V", "MOSI(5V)"), ("SCK in 5V", "SCK(5V)")], note="Nano outputs are 5 V, RA-02 inputs are 3.3 V.")
    s.module(870, 100, 280, "Arduino Nano", "signal handling / decoding (5 V)",
             left=[("D10", "NSS(5V)"), ("D9", "RST(5V)"), ("D11 MOSI", "MOSI(5V)"), ("D13 SCK", "SCK(5V)"), ("D12 MISO", "MISO"), ("D2", "DIO0")],
             right=[("D3 TX", "TX(5V)"), ("D4 RX", "RX"), ("D5", "LED_G"), ("D6", "LED_R"), ("D7", "BUZ"), ("GND", "GND")], color="#fffbeb")
    s.module(1300, 100, 220, "ESP32 DevKit", "WiFi / internet gateway", left=[("GPIO16 RX2", "TX"), ("GPIO17 TX2", "RX"), ("3V3 out", "3V3"), ("GND", "GND")], color="#eff6ff")
    s.module(1300, 290, 220, "Divider for Nano TX", "1 k + 2 k", left=[("in 5V", "TX(5V)"), ("out 3V3", "TX")])
    s.module(870, 330, 280, "Status + buzzer", "330 ohm per LED", left=[("GREEN rx", "LED_G"), ("RED err", "LED_R"), ("buzzer +", "BUZ"), ("GND", "GND")])
    s.t(40, 470, "Power: both boards from USB 5 V. Power RA-02 from the ESP32 3V3 pin, not the Nano (its 3V3 pin cannot supply TX current).", "note")
    s.t(40, 492, "Join all grounds. Antenna: SMA bulkhead on the enclosure to the mast helix.", "note")
    s.save(ROOT / "ground_station" / "circuit.svg"); s.pinmap(ROOT / "ground_station" / "pinmap.csv")


if __name__ == "__main__":
    cubesat(); burnwire(); tower(); ground(); print("schematics written")
