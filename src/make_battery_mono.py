#!/usr/bin/env python3
"""
Generates BatteryMono.ttf — a monochrome battery indicator font for SketchyBar.

Glyphs: Unicode PUA chr(0xF000 + pct) for pct in 0..100, plus chr(0xF065) for charging bolt
  - Each glyph shows a battery at the given charge percentage
  - Color controlled by icon.color in SketchyBar

Usage:
  python3 make_battery_mono.py [output.ttf]

Install font:
  cp BatteryMono.ttf ~/Library/Fonts/

SketchyBar usage:
  PCT=$(pmset -g batt | awk '/InternalBattery/ {gsub(/%/,"",  $3); print $3}')
  CHAR=$(python3 -c "print(chr(0xf000 + $PCT))")
  sketchybar --set item icon="$CHAR" icon.font="BatteryMono:Regular:16.0" icon.color=0xffe8761e
"""
import math
import argparse
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4

# ── Font metrics ───────────────────────────────────────────────────────────────
UPM     = 1000
ADVANCE = 1000
ASCENT  =  800
DESCENT = -200

# ── Coordinate mapping ────────────────────────────────────────────────────────
# Uniform scale (no stretching) mapped to the battery's own bounding box,
# not the wasteful 32×32 SVG canvas. Scale to fill the available width,
# then center the result on the EM optical midpoint (y=300).
#
# Battery SVG bounds:
_SVG_X0, _SVG_X1 = 2.3273, 29.2363   # shell left → nub tip
_SVG_CY          = (10.1 + 22.4) / 2  # battery vertical centre = 16.25

_S  = 900 / (_SVG_X1 - _SVG_X0)       # uniform scale ≈ 33.5  (fills 900 of 1000 x)
_X0 = 50                               # left margin
_CY = 300                              # EM optical centre (mid of ascent 800 / descent -200)

def fx(v):  return round(_X0 + (v - _SVG_X0) * _S)
def fy(v):  return round(_CY + (_SVG_CY - v) * _S)  # flip Y, centred
def fsx(v): return round(v * _S)
def fsy(v): return round(v * _S)

# ── Battery geometry (from battery.50/75/100percent.svg) ──────────────────────
#
# All coords in SVG space (32×32 viewBox, y increases downward).
#
# Outer rounded-rect shell
SHELL_L, SHELL_R  =  2.3273, 26.3182   # x left/right
SHELL_T, SHELL_B  = 10.1,    22.4      # y top/bottom (SVG: top < bottom)
SHELL_RX, SHELL_RY = 4.8272, 4.8182   # corner radii

# Inner hole (creates the ring-shaped outline)
HOLE_L, HOLE_R  =  3.7909, 24.8545
HOLE_T, HOLE_B  = 11.5637, 20.9364
HOLE_RX, HOLE_RY = 3.1364, 3.1545

# Nub (small protrusion on right side)
NUB_L, NUB_R  = 27.5545, 29.2363
NUB_T, NUB_B  = 13.9,    18.6

# Fill block (inner charge indicator)
# Left edge is fixed; right edge scales linearly with percentage.
#   right_straight(pct) = FILL_L + pct * FILL_SLOPE
# Derived by linear fit to the three SVG samples (50/75/100%).
FILL_L     =  4.8545       # left straight edge x (constant)
FILL_T     = 12.6182       # top y (constant, SVG)
FILL_B     = 19.8818       # bottom y (constant, SVG)
FILL_R     =  1.591        # corner radius (both x and y)
FILL_SLOPE =  0.189364     # SVG x-units per percent

def fill_right(pct):
    """Right straight edge of fill block in SVG x-coords."""
    return FILL_L + pct * FILL_SLOPE

# ── Bounding box (font coords) — pinned across all glyphs ─────────────────────
BB_X0 = fx(SHELL_L)    # 73
BB_X1 = fx(NUB_R)      # 914  (include nub)
BB_Y0 = fy(SHELL_B)    # 100  (bottom)
BB_Y1 = fy(SHELL_T)    # 484  (top)
LSB   = BB_X0


def draw_bounds_anchor(pen):
    """Two invisible 1×1 boxes that pin the bounding box for every glyph."""
    for bx, by in [(BB_X0, BB_Y0), (BB_X1 - 1, BB_Y1 - 1)]:
        pen.moveTo((bx,   by  ))
        pen.lineTo((bx+1, by  ))
        pen.lineTo((bx+1, by+1))
        pen.lineTo((bx,   by+1))
        pen.closePath()


def draw_rrect(pen, x0, y0, x1, y1, rx, ry, ccw=True):
    """
    Rounded rectangle in font coords (Y-up).
    (x0,y0) = bottom-left, (x1,y1) = top-right.
    ccw=True  → counter-clockwise winding (solid fill / outer boundary)
    ccw=False → clockwise winding (hole)
    Corners are quadratic beziers (TrueType-compatible).
    """
    rx = min(rx, (x1 - x0) / 2)
    ry = min(ry, (y1 - y0) / 2)
    if ccw:
        pen.moveTo(  (x0+rx, y0))
        pen.lineTo(  (x1-rx, y0))
        pen.qCurveTo((x1,    y0),    (x1, y0+ry))
        pen.lineTo(  (x1,    y1-ry))
        pen.qCurveTo((x1,    y1),    (x1-rx, y1))
        pen.lineTo(  (x0+rx, y1))
        pen.qCurveTo((x0,    y1),    (x0, y1-ry))
        pen.lineTo(  (x0,    y0+ry))
        pen.qCurveTo((x0,    y0),    (x0+rx, y0))
        pen.closePath()
    else:
        pen.moveTo(  (x1-rx, y0))
        pen.lineTo(  (x0+rx, y0))
        pen.qCurveTo((x0,    y0),    (x0, y0+ry))
        pen.lineTo(  (x0,    y1-ry))
        pen.qCurveTo((x0,    y1),    (x0+rx, y1))
        pen.lineTo(  (x1-rx, y1))
        pen.qCurveTo((x1,    y1),    (x1, y1-ry))
        pen.lineTo(  (x1,    y0+ry))
        pen.qCurveTo((x1,    y0),    (x1-rx, y0))
        pen.closePath()


def draw_battery_outline(pen):
    """Outer shell + inner hole + nub."""
    # Outer shell (CCW = filled)
    draw_rrect(pen,
        fx(SHELL_L), fy(SHELL_B), fx(SHELL_R), fy(SHELL_T),
        fsx(SHELL_RX), fsy(SHELL_RY), ccw=True)

    # Inner hole (CW = subtracts from fill)
    draw_rrect(pen,
        fx(HOLE_L), fy(HOLE_B), fx(HOLE_R), fy(HOLE_T),
        fsx(HOLE_RX), fsy(HOLE_RY), ccw=False)

    # Nub: D-shape (straight left edge, curved right side)
    x0, x1 = fx(NUB_L), fx(NUB_R)
    y0, y1 = fy(NUB_B), fy(NUB_T)
    ymid = (y0 + y1) // 2
    pen.moveTo(  (x0, y0))
    pen.qCurveTo((x1, y0), (x1, ymid))
    pen.qCurveTo((x1, y1), (x0, y1))
    pen.closePath()


def draw_battery_fill(pen, pct):
    """Charge level rectangle, scaled to pct (0–100)."""
    if pct <= 0:
        return
    rx = fill_right(pct)
    if fx(rx) <= fx(FILL_L):   # zero or negative width after scaling
        return
    # draw_rrect clamps corner radii automatically when block is narrow
    draw_rrect(pen,
        fx(FILL_L), fy(FILL_B), fx(rx), fy(FILL_T),
        fsx(FILL_R), fsy(FILL_R), ccw=True)


# ── Bolt / charging glyph (glyph index 101, U+F065) ──────────────────────────
#
# The SVG uses a mask: a larger "mask bolt" is cut out of the battery
# outline + fill, then the smaller "actual bolt" is drawn on top.
# In font non-zero-winding terms:
#   - mask bolt contour (CW, single instance) removes coverage from ring + fill
#   - actual bolt contour (CCW) restores coverage inside the bolt shape
# This leaves a thin gap between the two bolt outlines (the visible border).

def _cubic_pts(p0, p1, p2, p3, n=8):
    """Sample n+1 points along a cubic bezier."""
    pts = []
    for i in range(n + 1):
        t = i / n; mt = 1 - t
        x = mt**3*p0[0] + 3*mt**2*t*p1[0] + 3*mt*t**2*p2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt**2*t*p1[1] + 3*mt*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def _bolt_poly(path_svg, n=8):
    """
    Build a polygon from an SVG path description (list of ('M'|'L'|'C', ...)).
    Returns [(font_x, font_y), ...] in CCW winding (Y-up).
    The raw bolt paths in the SVG are CW in Y-down → CCW in Y-up after flipping.
    """
    pts = []
    cur = None
    for cmd, *args in path_svg:
        if cmd == 'M':
            cur = args[0]
            pts.append(cur)
        elif cmd == 'L':
            cur = args[0]
            pts.append(cur)
        elif cmd == 'C':
            p1, p2, p3 = args
            sampled = _cubic_pts(cur, p1, p2, p3, n)
            pts.extend(sampled[1:])   # skip duplicate start
            cur = p3
    return [(fx(x), fy(y)) for x, y in pts]


# Parsed from battery.100percent.bolt.svg  <path … d="M9.3 16.8637 C…">
_MASK_BOLT_SVG = [
    ('M', (9.3,     16.8637)),
    ('C', (9.3,     17.7728), (10.0455, 18.5),    (10.9636, 18.5)),
    ('L', (12.2545, 18.5)),
    ('L', (11.2364, 21.2455)),
    ('C', (10.5364, 23.1364), (12.9091, 24.4364), (14.1545, 22.8818)),
    ('L', (19.1454, 16.6091)),
    ('C', (19.4091, 16.2818), (19.5636, 15.9),    (19.5636, 15.4909)),
    ('C', (19.5636, 14.5818), (18.8182, 13.8546), (17.9,    13.8546)),
    ('L', (16.6091, 13.8546)),
    ('L', (17.6273, 11.1091)),
    ('C', (18.3273, 9.2182),  (15.9545, 7.9182),  (14.7091, 9.4728)),
    ('L', (9.7182,  15.7455)),
    ('C', (9.4545,  16.0727), (9.3,     16.4546),  (9.3,    16.8637)),
]

# Parsed from battery.100percent.bolt.svg  <path … d="M10.5364 16.8637 C…">
_ACTUAL_BOLT_SVG = [
    ('M', (10.5364, 16.8637)),
    ('C', (10.5364, 17.0909), (10.7182, 17.2546), (10.9545, 17.2546)),
    ('L', (14.0364, 17.2546)),
    ('L', (12.3909, 21.6728)),
    ('C', (12.1818, 22.2546), (12.8,    22.5727),  (13.1727, 22.1091)),
    ('L', (18.1545, 15.8455)),
    ('C', (18.2454, 15.7273), (18.3091, 15.6091),  (18.3091, 15.4909)),
    ('C', (18.3091, 15.2637), (18.1273, 15.1),     (17.8909, 15.1)),
    ('L', (14.8091, 15.1)),
    ('L', (16.4545, 10.6819)),
    ('C', (16.6636, 10.1),    (16.0454, 9.7818),   (15.6727, 10.2455)),
    ('L', (10.6909, 16.5)),
    ('C', (10.5909, 16.6273), (10.5364, 16.7455),  (10.5364, 16.8637)),
]


def draw_bolt_cutout(pen):
    """Mask-bolt as a CW hole (subtracts from ring + fill)."""
    pts = _bolt_poly(_MASK_BOLT_SVG)
    pts = list(reversed(pts))   # CCW → CW in font Y-up
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()


def draw_bolt_shape(pen):
    """Actual bolt as CCW (positive fill on top of the cutout)."""
    pts = _bolt_poly(_ACTUAL_BOLT_SVG)
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()


def build_font(out_path="BatteryMono.ttf"):
    # 101 charge-level glyphs (0–100) + 1 charging/bolt glyph (101)
    N = 102
    glyph_order = [".notdef"] + [f"bat{i}" for i in range(N)]
    cmap_map    = {0xF000 + i: f"bat{i}" for i in range(N)}

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap_map)

    glyphs  = {}
    metrics = {}

    pen = TTGlyphPen(None)
    pen.moveTo((100, 0)); pen.lineTo((100, 700))
    pen.lineTo((400, 700)); pen.lineTo((400, 0))
    pen.closePath()
    glyphs[".notdef"]  = pen.glyph()
    metrics[".notdef"] = (ADVANCE, 0)

    for i in range(N):
        pen = TTGlyphPen(None)
        draw_bounds_anchor(pen)
        if i < 101:
            draw_battery_outline(pen)
            draw_battery_fill(pen, i)
        else:
            # Glyph 101 (U+F065): 100% battery with bolt (charging indicator)
            draw_battery_outline(pen)
            draw_battery_fill(pen, 100)
            draw_bolt_cutout(pen)   # CW hole in ring + fill
            draw_bolt_shape(pen)    # CCW bolt on top
        glyphs[f"bat{i}"]  = pen.glyph()
        metrics[f"bat{i}"] = (ADVANCE, LSB)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASCENT, descent=DESCENT)
    fb.setupNameTable({
        "familyName":           "BatteryMono",
        "styleName":            "Regular",
        "uniqueFontIdentifier": "1.000;CUST;BatteryMono",
        "fullName":             "BatteryMono",
        "version":              "Version 1.000",
        "psName":               "BatteryMono",
    })
    fb.setupOS2(
        sTypoAscender=ASCENT, sTypoDescender=DESCENT, sTypoLineGap=0,
        usWinAscent=ASCENT, usWinDescent=abs(DESCENT),
        sxHeight=500, sCapHeight=700,
        achVendID="CUST", fsType=0, fsSelection=0x40,
    )
    fb.setupPost(keepGlyphNames=False)
    fb.setupHead(unitsPerEm=UPM)

    font = fb.font
    font["head"].flags = 0b00001011

    mac_cmap = cmap_format_4(4)
    mac_cmap.platformID = 1
    mac_cmap.platEncID  = 0
    mac_cmap.language   = 0
    mac_cmap.cmap       = {0x20: ".notdef"}
    font["cmap"].tables.append(mac_cmap)

    gasp = newTable("gasp")
    gasp.version   = 1
    gasp.gaspRange = {65535: 15}
    font["gasp"] = gasp

    font.save(out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build BatteryMono.ttf")
    parser.add_argument("output", nargs="?", default="BatteryMono.ttf")
    args = parser.parse_args()
    build_font(args.output)
    print()
    print("Install:  cp", args.output, "~/Library/Fonts/")
