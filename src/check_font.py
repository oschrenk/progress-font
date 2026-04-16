#!/usr/bin/env python3
"""
Validate ProgressRingMono.ttf — checks that the font will be accepted by
CoreText / Font Book without errors.

Run:  uv run --with fonttools python3 check_font.py [ProgressRingMono.ttf]
Exit: 0 = pass, 1 = fail
"""
import sys
from fontTools.ttLib import TTFont

REQUIRED_TABLES  = {"head", "hhea", "hmtx", "cmap", "loca", "maxp", "glyf", "name", "post", "OS/2"}
REQUIRED_NAME_IDS = {
    1: "familyName",
    2: "styleName",
    3: "uniqueFontIdentifier",
    4: "fullName",
    5: "version",
    6: "psName",
}
EXPECTED_GLYPHS  = 101   # arc0 .. arc100
EXPECTED_ADVANCE = 1000  # monowidth


def check(path):
    errors = []
    f = TTFont(path)

    # Required tables
    missing = REQUIRED_TABLES - set(f.keys())
    if missing:
        errors.append(f"Missing required tables: {sorted(missing)}")

    # Name table completeness
    present_ids = {r.nameID for r in f["name"].names}
    for nid, label in REQUIRED_NAME_IDS.items():
        if nid not in present_ids:
            errors.append(f"name table missing nameID {nid} ({label})")

    # post table format (3.0 = no glyph names, valid and compact)
    post_fmt = f["post"].formatType
    if post_fmt not in (2.0, 3.0):
        errors.append(f"post.formatType={post_fmt!r} (expected 2.0 or 3.0)")

    # Glyph count (fontTools renames PUA glyphs to uniXXXX from cmap)
    glyph_order = f.getGlyphOrder()
    # non-.notdef glyphs are the 101 progress glyphs
    progress_glyphs = [g for g in glyph_order if g != ".notdef"]
    if len(progress_glyphs) != EXPECTED_GLYPHS:
        errors.append(f"Expected {EXPECTED_GLYPHS} progress glyphs, got {len(progress_glyphs)}")

    # Monowidth: all progress glyphs must share the same advance
    hmtx = f["hmtx"].metrics
    bad_advance = [
        g for g in progress_glyphs
        if hmtx.get(g, (0,))[0] != EXPECTED_ADVANCE
    ]
    if bad_advance:
        errors.append(f"Non-monowidth glyphs (advance != {EXPECTED_ADVANCE}): {bad_advance[:5]}")

    # Codepoint coverage: U+E000..U+E064
    cmap = f.getBestCmap()
    missing_cp = [cp for cp in range(0xE000, 0xE065) if cp not in cmap]
    if missing_cp:
        errors.append(f"Missing codepoints: {[hex(c) for c in missing_cp[:5]]} ...")

    return errors


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "ProgressRingMono.ttf"
    print(f"Checking {path} ...")
    errors = check(path)
    if errors:
        print("FAIL")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    else:
        print("OK — font passes all checks")


if __name__ == "__main__":
    main()
