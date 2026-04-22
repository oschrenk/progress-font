# Progress Font

A fixed-width icon font collection for [SketchyBar](https://github.com/FelixKratz/SketchyBar) and similar tools.

## Fonts

### Progress Ring

101 circular progress ring glyphs (0–100%).

| Variant | Font name | Color |
|---------|-----------|-------|
| **Mono** | `ProgressRingMono` | Set via `icon.color` in your config |
| **Color** | `ProgressRingColor` | Two colors baked at build time (arc + background track) |

Glyph encoding: `U+E000 + pct` for `pct` in 0–100.

```lua
local function pct_to_glyph(pct)
  return utf8.char(0xE000 + math.max(0, math.min(100, math.floor(pct))))
end
```

---

### Battery

102 battery glyphs — one per charge percentage plus a charging indicator.

| Glyph | Codepoint | Description |
|-------|-----------|-------------|
| 0%–100% | `U+F000 + pct` | Battery at exact charge level |
| Charging | `U+F065` | 100% battery with lightning bolt |

```lua
local function pct_to_glyph(pct)
  return utf8.char(0xF000 + math.max(0, math.min(101, math.floor(pct))))
end

local CHARGING_GLYPH = pct_to_glyph(101)  -- U+F065
```

See `examples/BatteryMonoExample.lua` for a complete SketchyBar item. Recommended font size: **24pt**.

---

## Quick start

```bash
# Progress Ring
task install-mono        # or: task install-color
sketchybar --reload

# Battery
task install-battery-mono
sketchybar --reload
```

---

## All tasks

| Command | Description |
|---------|-------------|
| `task build-mono` | Build `build/ProgressRingMono.ttf` |
| `task install-mono` | Build + install + flush font cache |
| `task build-color` | Build `build/ProgressRingColor.ttf` |
| `task install-color` | Build + install color font + flush font cache |
| `task build-battery-mono` | Build `build/BatteryMono.ttf` |
| `task install-battery-mono` | Build + install battery font + flush font cache |
| `task check-mono` | Validate ProgressRingMono structure and glyph coverage |
| `task fontbook-mono` | Open ProgressRingMono in Font Book |
| `task test` | Install mono + open browser test page |
| `task clean` | Remove all built fonts |

---

## Build args

### ProgressRingMono / ProgressRingColor

```bash
task install-mono [THICKNESS=N]
task install-color [FG=rrggbbaa] [BG=rrggbbaa] [THICKNESS=N]
```

| Variable | Default | Description |
|----------|---------|-------------|
| `THICKNESS` | `120` | Ring thickness in font units (outer radius is 420) |
| `FG` | `e8dcb7ff` | Arc color (Color variant only) |
| `BG` | `48484878` | Background ring color (Color variant only) |

> **Color variant:** set `icon.color = 0xffffffff` in sketchybar — anything other than white tints the baked CPAL palette colors.

### Color variants (e.g. alert state)

Build a second font with different colors — see the `build-alert` / `install-alert` template in `taskfile.yml`:

```lua
local family = charge < 20 and "ProgressRingAlert" or "ProgressRingColor"
ring:set({ icon = { string = pct_to_glyph(charge),
                    font = { family = family, style = "Regular", size = 24.0 } } })
```

---

## Troubleshooting

**Tofu / question mark after install:**
macOS's `fontd` caches font metadata aggressively. `task install-*` runs `pkill -f fontd` automatically. If the problem persists:

```bash
pkill -9 fontd
sleep 2
brew services restart sketchybar
```

> **Do NOT use `sudo atsutil databases -remove`** — it wipes the cache for all fonts including SF Symbols, breaking your entire bar until fontd re-indexes everything.

**Font shows in Font Book but not in sketchybar:**
fontd may have a stale cached version. Run `pkill -9 fontd && sleep 2 && sketchybar --reload`.

**Font Book shows validation errors:**
Rebuild with the relevant `task build-*`. Also check `~/.Trash/` for old versions — Font Book scans the Trash and can pick up deleted fonts.
