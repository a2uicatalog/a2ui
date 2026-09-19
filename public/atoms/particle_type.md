# Particle Type

Agentic typeface: the words an agent supplies assemble out of thousands of coloured particles that fly in from random positions and settle into the letterforms; the pointer scatters them and they reform. Text is rasterised on an offscreen canvas and sampled into particle targets, so any string works, at any panel size, in a system font. Honours prefers-reduced-motion (renders the settled word), pauses offscreen, DPR-aware. The words are also emitted as visually-hidden text so they stay readable and selectable. Sibling of light_type (words as flowing light) and living_type (letters that breathe). Every option is an enum or a clamped int; text is JSON-encoded into the script with "<" escaped, so it can never break out.

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
| density | "low" | "normal" | "high"  (optional, default "normal"). Particle count cap 1200 / 2400 / 4200. |
| dot | "fine" | "normal" | "bold"  (optional, default "normal"). Particle radius. |

## Example payload

```json
{
  "type": "particle_type"
}
```

Live page: https://a2uicatalog.ai/atoms/particle_type/
Full field contract: https://a2uicatalog.ai/spec.json
