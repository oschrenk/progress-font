#!/usr/bin/env python3
"""
Generates ProgressRingMono.ttf — a single-color progress arc font for SketchyBar.

Glyphs: Unicode PUA chr(0xE000 + pct) for pct in 0..100
  - Each glyph is just the filled arc sector (clockwise from 12 o'clock)
  - 0% = empty glyph, 100% = full ring
  - Color controlled entirely by icon.color in SketchyBar

Usage:
  python3 make_progress_ring_mono.py [output.ttf] [--thickness N]

  --thickness  ring thickness in font units 1-419  (default: 120)

Install font:
  cp ProgressRingMono.ttf ~/Library/Fonts/
"""
import sys
import argparse
from fontTools.ttLib import TTFont, newTable
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4

from progress_ring_geometry import (
    UPM, ADVANCE, CX, OUTER_R, INNER_R,
    draw_bounds_anchor, draw_arc_ring,
)


def build_font(out_path="ProgressRingMono.ttf", inner_r=None):
    if inner_r is None:
        inner_r = INNER_R

    glyph_order = [".notdef"] + [f"arc{i}" for i in range(101)]
    cmap_map    = {0xE000 + i: f"arc{i}" for i in range(101)}
    lsb         = CX - OUTER_R  # 80

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

    for i in range(101):
        pen = TTGlyphPen(None)
        draw_bounds_anchor(pen)
        draw_arc_ring(pen, i, inner_r=inner_r)
        glyphs[f"arc{i}"]  = pen.glyph()
        metrics[f"arc{i}"] = (ADVANCE, lsb)

    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({
        "familyName":           "ProgressRingMono",
        "styleName":            "Regular",
        "uniqueFontIdentifier": "1.000;CUST;ProgressRingMono",
        "fullName":             "ProgressRingMono",
        "version":              "Version 1.000",
        "psName":               "ProgressRingMono",
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
    parser = argparse.ArgumentParser(description="Build ProgressRingMono.ttf")
    parser.add_argument("output", nargs="?", default="ProgressRingMono.ttf")
    parser.add_argument("--thickness", type=int, default=None,
                        help=f"ring thickness in font units 1-{OUTER_R-1} (default: {OUTER_R - INNER_R})")
    args = parser.parse_args()

    inner_r = None
    if args.thickness is not None:
        inner_r = OUTER_R - args.thickness

    build_font(args.output, inner_r=inner_r)
    print()
    print("Install:  cp", args.output, "~/Library/Fonts/")
    print()
    print("SketchyBar usage:")
    print('  PCT=75')
    print('  CHAR=$(python3 -c "print(chr(0xe000 + $PCT))")')
    print('  sketchybar --set item icon="$CHAR" icon.font="ProgressRingMono:Regular:16.0" icon.color=0xffe8761e')
