-- ProgressRingExample.lua
-- Displays battery percentage as a two-color progress ring using ProgressRingColor.ttf.
-- Font must be installed: task install-color (from progress-font repo)
--
-- Add to sketchybarrc:
--   require("items.ProgressRingExample").new().add("right")

local sbar = require("sketchybar")

local function pct_to_glyph(pct)
  -- U+E000 = 0%, U+E001 = 1%, ..., U+E064 = 100%
  pct = math.max(0, math.min(100, math.floor(pct)))
  return utf8.char(0xE000 + pct)
end

local ProgressRingExample = {}

function ProgressRingExample.new()
  local self = {}

  self.add = function(position)
    local ring = sbar.add("item", {
      position = position,
      icon = {
        font = {
          family = "ProgressRingColor",
          style = "Regular",
          size = 24.0,
        },
        color = 0xffffffff, -- must be white to let COLR palette colors through
        string = pct_to_glyph(0),
        y_offset = -3,
        width = 24,
      },
      label = { drawing = false },
      update_freq = 60,
    })

    local function update()
      sbar.exec("pmset -g batt", function(batt_info)
        local _, _, charge = batt_info:find("(%d+)%%")
        if charge then
          ring:set({ icon = { string = pct_to_glyph(tonumber(charge)) } })
        end
      end)
    end

    ring:subscribe({ "routine", "power_source_change", "system_woke" }, update)
    update()
  end

  return self
end

return ProgressRingExample
