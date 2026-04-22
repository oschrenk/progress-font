-- BatteryMonoExample.lua
-- SketchyBar battery item using BatteryMono.ttf
--
-- Font glyphs:
--   U+F000 + pct  →  battery at exact charge level (pct = 0..100)
--   U+F065        →  battery at 100% with charging bolt
--
-- Install font first:
--   task install-battery-mono
--
-- Usage in your bar config:
--   local Battery = require("items/BatteryMono")
--   Battery.new():add("right")

local sbar = require("sketchybar")

local FONT_FAMILY = "BatteryMono"
local FONT_STYLE  = "Regular"
local FONT_SIZE   = 24.0

-- U+F065 = glyph index 101 in the font (reuses the same encoding helper below)
local CHARGING_GLYPH  -- set after pct_to_glyph is defined

local function pct_to_glyph(pct)
  -- U+F000 + pct: encoded as UTF-8 (U+F000..U+F064 → 3-byte sequences)
  pct = math.max(0, math.min(100, math.floor(pct)))
  local codepoint = 0xF000 + pct
  -- UTF-8 encode: U+F000–U+FFFF → 0xEF 0xBC/... (3 bytes)
  local b1 = 0xE0 + math.floor(codepoint / 0x1000)
  local b2 = 0x80 + math.floor((codepoint % 0x1000) / 0x40)
  local b3 = 0x80 + (codepoint % 0x40)
  return string.char(b1, b2, b3)
end

CHARGING_GLYPH = pct_to_glyph(101)   -- U+F065: 100% battery with bolt

local Battery = {}

function Battery.new()
  local self = {}

  self.add = function(position)
    local battery = sbar.add("item", {
      position   = position,
      label      = { drawing = false },
      icon       = {
        font = { family = FONT_FAMILY, style = FONT_STYLE, size = FONT_SIZE },
        string = pct_to_glyph(0),
      },
      update_freq = 120,
    })

    battery:subscribe("mouse.clicked", function(_)
      sbar.exec("open 'x-apple.systempreferences:com.apple.preference.battery'")
    end)

    battery:subscribe({ "routine", "power_source_change", "system_woke" }, function()
      sbar.exec("pmset -g batt", function(batt_info)
        local charging = string.find(batt_info, "AC Power") ~= nil
        local _, _, charge_str = batt_info:find("(%d+)%%")
        local pct = charge_str and tonumber(charge_str) or 0

        local glyph = charging and CHARGING_GLYPH or pct_to_glyph(pct)

        -- Optional: color shifts by charge level when on battery
        local color
        if charging then
          color = 0xffe8761e   -- orange while charging
        elseif pct <= 10 then
          color = 0xffff3b30   -- red: critically low
        elseif pct <= 20 then
          color = 0xffff9f0a   -- amber: low
        else
          color = 0xffe8dcb7ff -- your default foreground color
        end

        battery:set({
          icon = {
            string = glyph,
            color  = color,
          },
        })
      end)
    end)
  end

  return self
end

return Battery
