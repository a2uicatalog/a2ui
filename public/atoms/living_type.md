# Living Type

Agentic typeface: the words an agent supplies are set glyph by glyph on canvas and every letter breathes on its own noise track -- drifting, tilting and scaling a little, so the headline feels alive rather than animated. Letters lean toward the pointer and swell as it passes. Works on light or dark backgrounds (set background and colors). Honours prefers-reduced-motion (renders one static frame), pauses offscreen, DPR-aware; the words are also emitted as visually-hidden text. Sibling of particle_type and light_type. Every option is an enum or a clamped int; text is JSON-encoded into the script with "<" escaped.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string (required). The words to set, up to 3 lines separated by "\n", each trimmed to 40 characters. Short and bold reads best. Default "A2UI". |
| font | "sans" | "serif" | "mono" | "display"  (optional, default "sans"). System font stacks; no webfont is loaded. |
| weight | "regular" | "bold" | "black"  (optional, default "black") |
| colors | array of 1-4 "#rrggbb" strings (optional). Default ["#38bdf8","#818cf8","#f472b6"], applied left to right across the words. Invalid entries are dropped. |
| background | "#rrggbb" (optional). Default "#070a12". |
| height | integer (optional). Panel height in px, clamped 160-900. |
| interactive | bool (optional). Pointer affects the letters. Default true. |
| motion | "subtle" | "normal" | "wild"  (optional, default "normal"). Drift amplitude. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |

## Example payload

```json
{
  "type": "living_type"
}
```

Live page: https://a2uicatalog.ai/atoms/living_type/
Full field contract: https://a2uicatalog.ai/spec.json
