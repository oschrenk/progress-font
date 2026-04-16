# Progress Ring Font

A fixed-width icon font with 101 circular progress ring glyphs (0–100%), for use in [SketchyBar](https://github.com/FelixKratz/SketchyBar) and similar tools.

Two variants are available:

| Variant | Font name | Color | Use when |
|---------|-----------|-------|----------|
| **Mono** | `ProgressRingMono` | Color set via `icon.color` in your config | You want to tint the ring from your sketchybar config |
| **Color** | `ProgressRingColor` | Two colors baked at build time (arc + ring background) | You want a styled ring with a colored background track |

---

## Quick start

### Mono (with "runtime" color)

A plain glyph font — color works the same as any other icon, set via `icon.color`.

```bash
task install-mono
sketchybar --reload
```

```lua
local ring = sbar.add("item", {
  icon = {
    font  = { family = "ProgressRingMono", style = "Regular", size = 20.0 },
    color = 0xffe8761e,  -- controls the entire glyph; change freely in your config
  },
})
ring:set({ icon = { string = utf8.char(0xE000 + 75) } })  -- 75%
```

### Color (two-color, baked at build time)

```bash
task install-color   # uses defaults from Taskfile (FG and BG vars)
sketchybar --reload
```

```lua
local ring = sbar.add("item", {
  icon = {
    font  = { family = "ProgressRingColor", style = "Regular", size = 20.0 },
    color = 0xffffffff,  -- MUST be white — lets the baked CPAL colors show through
  },
})
ring:set({ icon = { string = utf8.char(0xE000 + 75) } })  -- 75%
```

> **Why white?** `ProgressRingColor` uses the COLR/CPAL font format — colors are embedded
> in the font's palette table. SketchyBar's `icon.color` is multiplied on top, so anything
> other than white (0xffffffff) will tint or completely override the baked colors.

---

## Build args

### Mono

```bash
task build-mono [THICKNESS=N]
task install-mono [THICKNESS=N]
```

| Variable | Default | Description |
|----------|---------|-------------|
| `THICKNESS` | `120` | Ring thickness in font units (outer radius is 420) |

```bash
task install-mono                  # default thickness
task install-mono THICKNESS=80     # thinner ring
task install-mono THICKNESS=160    # thicker ring
```

### Color

```bash
task build-color [FG=rrggbbaa] [BG=rrggbbaa] [THICKNESS=N]
task install-color [FG=rrggbbaa] [BG=rrggbbaa] [THICKNESS=N]
```

| Variable | Default (Taskfile) | Description |
|----------|--------------------|-------------|
| `FG` | `e8dcb7ff` | Arc color — `RRGGBBAA` hex, fully opaque recommended |
| `BG` | `48484878` | Background ring color — `RRGGBBAA` hex, alpha controls visibility |
| `THICKNESS` | `120` | Ring thickness in font units (outer radius is 420) |

Colors are baked into the font at build time — to change them, rebuild and reinstall.

```bash
task install-color                                   # Taskfile defaults
task install-color FG=00bfffff                       # blue arc
task install-color BG=ffffff20 FG=ff3b30ff           # red arc, faint white ring
task install-color THICKNESS=80 FG=30d158ff          # thin green arc
task install-color THICKNESS=140 FG=ff3b30ff         # thick red arc (e.g. low battery alert)
```

---

## Glyph encoding

| Percentage | Codepoint |
|------------|-----------|
| 0%         | U+E000    |
| 50%        | U+E032    |
| 75%        | U+E04B    |
| 100%       | U+E064    |

Formula: `U+E000 + pct` for `pct` in 0–100.

```lua
local function pct_to_glyph(pct)
  pct = math.max(0, math.min(100, math.floor(pct)))
  return utf8.char(0xE000 + pct)
end
```

---

## All tasks

| Command | Description |
|---------|-------------|
| `task build-mono` | Build `build/ProgressRingMono.ttf` |
| `task install-mono` | Build + install to `~/Library/Fonts/` + flush font cache |
| `task build-color` | Build `build/ProgressRingColor.ttf` |
| `task install-color` | Build + install color font + flush font cache |
| `task check-mono` | Validate font structure and glyph coverage |
| `task fontbook-mono` | Open in Font Book |
| `task test` | Install mono + open browser test page |
| `task clean` | Remove built fonts |

---

## Adding color variants (e.g. alert state)

To use a different color for low battery, build a second font with a different name — see
the commented `build-alert` / `install-alert` template in `taskfile.yml`.

Then switch the font family in Lua based on state:

```lua
local family = charge < 20 and "ProgressRingAlert" or "ProgressRingColor"
ring:set({ icon = { string = pct_to_glyph(charge),
                    font = { family = family, style = "Regular", size = 24.0 } } })
```

---

## Troubleshooting

**[Tofu](https://en.wikipedia.org/wiki/Noto_fonts#Tofu) / question mark in sketchybar after install:**
macOS's `fontd` daemon caches font metadata aggressively. Even after replacing a font file,
the old data stays cached until the daemon restarts. `task install-*` runs `pkill -f fontd`
automatically. If tofu persists after install:

```bash
pkill -f fontd
sleep 5
brew services restart sketchybar
```

> **Do NOT use `sudo atsutil databases -remove`** — it wipes the cache for ALL fonts
> including SF Symbols and system fonts, breaking your entire bar until fontd re-indexes
> everything (takes 30–60 seconds and requires a sketchybar restart).

**Font shows in Font Book but not in sketchybar:**
fontd may have loaded a stale cached version before your new file was registered.
The `pkill -f fontd` in the install task handles this. You can verify the font loaded
correctly with:

```bash
swiftc /dev/stdin -o /tmp/ftest <<'EOF'
import AppKit
let f = NSFont(name: "ProgressRingColor", size: 20)
print(f?.fontName ?? "NOT FOUND")
EOF
/tmp/ftest
```

If it prints a hash like `font000000002f915a10` instead of the font name, fontd still
has the stale cache — run `pkill -f fontd && sleep 5`.

**Font Book shows validation errors:**
Rebuild with `task build-color` or `task build-mono`. If errors persist, check that old
versions aren't lurking in the Trash (`~/.Trash/ProgressRing*.ttf`) — Font Book scans
the Trash and can pick up deleted fonts.

