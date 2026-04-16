#!/usr/bin/env python3
"""
Generates ProgressRingColor.ttf — a COLR/CPAL two-color icon font for SketchyBar.

Glyphs: Unicode PUA chr(0xE000 + pct) for pct in 0..100
  - Layer 0: full ring (background color)
  - Layer 1: arc clockwise from 12 o'clock (foreground color)

Colors are baked into the font's CPAL table. In SketchyBar set icon.color=0xffffffff
(white) to let the CPAL colors show through unmodified.

Usage:
  python3 make_progress_ring_color.py [output.ttf] [--bg RRGGBBAA] [--fg RRGGBBAA]

  --bg   background ring color as RRGGBBAA hex  (default: 96969678 = gray 55% alpha)
  --fg   foreground arc color as RRGGBBAA hex   (default: e6731eff = orange)

Examples:
  python3 make_progress_ring_color.py                          # defaults
  python3 make_progress_ring_color.py out.ttf --fg 00ff00ff   # green arc
  python3 make_progress_ring_color.py out.ttf --bg ffffff30 --fg e8761eff
"""
import sys
import argparse
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools import ttLib
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.ttLib.tables.C_P_A_L_ import Color
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from types import SimpleNamespace

from progress_ring_geometry import (
    UPM, ADVANCE, CX, OUTER_R, INNER_R,
    draw_bounds_anchor, draw_full_ring, draw_arc_ring,
)


def parse_color(hex_str):
    """Parse RRGGBBAA hex string → CPAL (B, G, R, A) tuple."""
    h = hex_str.lstrip("#")
    if len(h) != 8:
        raise ValueError(f"Color must be RRGGBBAA hex, got: {hex_str!r}")
    r, g, b, a = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
    return (b, g, r, a)  # fontTools CPAL byte order


def build_font(out_path="ProgressRingColor.ttf", bg_color=None, fg_color=None, inner_r=None):
    # ring{i}  — cmap-mapped glyphs with bounds anchor (COLR base)
    # bg{i}    — full donut geometry (gray COLR layer)
    # arc{i}   — partial arc geometry (orange COLR layer)
    glyph_order = ([".notdef"] +
                   [f"ring{i}" for i in range(101)] +
                   [f"bg{i}"   for i in range(101)] +
                   [f"arc{i}"  for i in range(101)])

    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({0xE000 + i: f"ring{i}" for i in range(101)})

    if inner_r is None:
        inner_r = INNER_R

    glyphs  = {}
    metrics = {}
    LSB = CX - OUTER_R  # 80

    # .notdef
    pen = TTGlyphPen(None)
    pen.moveTo((100, 0)); pen.lineTo((100, 700))
    pen.lineTo((400, 700)); pen.lineTo((400, 0))
    pen.closePath()
    glyphs[".notdef"]  = pen.glyph()
    metrics[".notdef"] = (ADVANCE, 0)

    for i in range(101):
        # Base glyph: bounds anchor only — COLR layers provide visuals
        pen = TTGlyphPen(None)
        draw_bounds_anchor(pen)
        glyphs[f"ring{i}"]  = pen.glyph()
        metrics[f"ring{i}"] = (ADVANCE, LSB)

        # Background layer: full donut ring + bounds anchor
        pen = TTGlyphPen(None)
        draw_bounds_anchor(pen)
        draw_full_ring(pen, inner_r=inner_r)
        glyphs[f"bg{i}"]  = pen.glyph()
        metrics[f"bg{i}"] = (ADVANCE, LSB)

        # Foreground layer: arc + bounds anchor (keeps bbox consistent across all pcts)
        pen = TTGlyphPen(None)
        draw_bounds_anchor(pen)
        if i > 0:
            draw_arc_ring(pen, i, inner_r=inner_r)
        glyphs[f"arc{i}"]  = pen.glyph()
        metrics[f"arc{i}"] = (ADVANCE, LSB)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({
        "familyName":           "ProgressRingColor",
        "styleName":            "Regular",
        "uniqueFontIdentifier": "1.000;CUST;ProgressRingColor",
        "fullName":             "ProgressRingColor",
        "version":              "Version 1.000",
        "psName":               "ProgressRingColor",
    })
    fb.setupOS2(
        sTypoAscender=800, sTypoDescender=-200, sTypoLineGap=0,
        usWinAscent=800, usWinDescent=200,
        sxHeight=500, sCapHeight=700,
        achVendID="CUST", fsType=0, fsSelection=0x40,
    )
    fb.setupPost(keepGlyphNames=False)
    fb.setupHead(unitsPerEm=UPM)

    font = fb.font

    # Fix head.flags to match working icon fonts
    font["head"].flags = 0b00001011

    # Add Mac platform cmap
    mac_cmap = cmap_format_4(4)
    mac_cmap.platformID = 1
    mac_cmap.platEncID  = 0
    mac_cmap.language   = 0
    mac_cmap.cmap       = {0x20: ".notdef"}
    font["cmap"].tables.append(mac_cmap)

    # gasp: smoothing at all sizes
    gasp = ttLib.newTable("gasp")
    gasp.version   = 1
    gasp.gaspRange = {65535: 15}
    font["gasp"] = gasp

    # CPAL: two-color palette
    _bg = bg_color or (150, 150, 150, 120)  # default: translucent gray
    _fg = fg_color or ( 30, 115, 230, 255)  # default: orange (RGB 230,115,30)
    cpal = ttLib.newTable("CPAL")
    cpal.version           = 0
    cpal.numPaletteEntries = 2
    cpal.palettes          = [[Color(*_bg), Color(*_fg)]]
    cpal.paletteLabels     = []
    cpal.paletteEntryLabels = []
    font["CPAL"] = cpal

    # COLR v0: map each ring{i} to [bg{i} + arc{i}]
    colr = ttLib.newTable("COLR")
    colr.version = 0
    colr.ColorLayers = {
        f"ring{i}": [
            SimpleNamespace(name=f"bg{i}",  colorID=0),
            SimpleNamespace(name=f"arc{i}", colorID=1),
        ]
        for i in range(101)
    }
    font["COLR"] = colr

    font.save(out_path)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build ProgressRingColor.ttf")
    parser.add_argument("output", nargs="?", default="ProgressRingColor.ttf")
    parser.add_argument("--bg", metavar="RRGGBBAA", help="background ring color (default: 96969678)")
    parser.add_argument("--fg", metavar="RRGGBBAA", help="foreground arc color  (default: e6731eff)")
    parser.add_argument("--thickness", type=int, default=None,
                        help=f"ring thickness in font units 1-{OUTER_R-1} (default: {OUTER_R - INNER_R})")
    args = parser.parse_args()

    bg      = parse_color(args.bg) if args.bg else None
    fg      = parse_color(args.fg) if args.fg else None
    inner_r = (OUTER_R - args.thickness) if args.thickness is not None else None

    build_font(args.output, bg_color=bg, fg_color=fg, inner_r=inner_r)
    print()
    print("Install:  cp", args.output, "~/Library/Fonts/")
    print()
    print("SketchyBar usage:")
    print('  PCT=75')
    print('  CHAR=$(python3 -c "print(chr(0xe000 + $PCT))")')
    print('  sketchybar --set item icon="$CHAR" icon.font="ProgressRingColor:Regular:16.0" icon.color=0xffffffff')
