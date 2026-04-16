"""Shared geometry for ProgressRing font variants."""
import math

UPM          = 1000
CX, CY       = 500, 480   # center
OUTER_R      = 420
INNER_R      = 300        # default inner radius → thickness = 120 units
ADVANCE      = 1000
SEGS         = 72          # polygon segments for full circle


def arc_pts(cx, cy, r, deg_start, deg_end, n):
    """n+1 equally-spaced points along an arc."""
    pts = []
    for i in range(n + 1):
        a = math.radians(deg_start + (deg_end - deg_start) * i / n)
        pts.append((round(cx + r * math.cos(a)), round(cy + r * math.sin(a))))
    return pts


def draw_bounds_anchor(pen):
    """Two invisible 1×1 unit boxes pinning the full ring bounding box.

    Forces every glyph to report xMin=CX-OUTER_R, xMax=CX+OUTER_R,
    yMin=CY-OUTER_R, yMax=CY+OUTER_R regardless of how much arc is drawn.
    Without this, partial arcs have smaller bounding boxes and renderers
    (sketchybar/CoreText) position each glyph differently, breaking monowidth.
    At any real font size (≥10px) these boxes are <0.1px — completely invisible.
    """
    x0, y0 = CX - OUTER_R,     CY - OUTER_R      # bottom-left  (80,  60)
    x1, y1 = CX + OUTER_R - 1, CY + OUTER_R - 1  # top-right   (919, 899)
    pen.moveTo((x0,     y0    ))
    pen.lineTo((x0 + 1, y0    ))
    pen.lineTo((x0 + 1, y0 + 1))
    pen.lineTo((x0,     y0 + 1))
    pen.closePath()
    pen.moveTo((x1,     y1    ))
    pen.lineTo((x1 + 1, y1    ))
    pen.lineTo((x1 + 1, y1 + 1))
    pen.lineTo((x1,     y1 + 1))
    pen.closePath()


def draw_full_ring(pen, inner_r=None):
    """Full donut as a single contour: outer CCW then inner CW, bridged at 0°."""
    if inner_r is None:
        inner_r = INNER_R
    outer = arc_pts(CX, CY, OUTER_R, 0, 359.9, SEGS)
    inner = arc_pts(CX, CY, inner_r, 359.9, 0, SEGS)
    pen.moveTo(outer[0])
    for p in outer[1:]:
        pen.lineTo(p)
    pen.lineTo(inner[0])
    for p in inner[1:]:
        pen.lineTo(p)
    pen.closePath()


def draw_arc_ring(pen, pct, inner_r=None):
    """Partial donut arc for pct 0-100, clockwise from 12 o'clock."""
    if pct <= 0:
        return  # truly empty — caller must handle empty glyph
    if inner_r is None:
        inner_r = INNER_R
    pct   = min(pct, 100)
    start = 90                    # 12 o'clock in font coords (Y-up)
    end   = start - pct * 3.6    # clockwise on screen
    n     = max(1, int(SEGS * pct / 100))
    outer = arc_pts(CX, CY, OUTER_R, start, end, n)
    inner = arc_pts(CX, CY, inner_r, start, end, n)
    pen.moveTo(outer[0])
    for p in outer[1:]:
        pen.lineTo(p)
    pen.lineTo(inner[-1])
    for p in reversed(inner[:-1]):
        pen.lineTo(p)
    pen.closePath()
