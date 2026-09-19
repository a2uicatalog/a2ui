# Light Type

Agentic typeface: the words an agent supplies are rendered as flowing light -- luminous streams ride a noise field inside the letterforms only (particles spawn on the glyph mask and respawn when they leave it), drawn with additive long-exposure trails and composited through the text as a mask, with a soft glow halo behind. Reads as a headline made of moving liquid light. Pointer swirls the flow. Honours prefers-reduced-motion (one pre-simulated frame), pauses offscreen, DPR-aware; the words are also emitted as visually-hidden text. Dark backgrounds only -- trails are additive. Sibling of particle_type and living_type. Every option is an enum or a clamped int; text is JSON-encoded into the script with "<" escaped.

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
| density | "low" | "normal" | "high"  (optional, default "normal"). Streams per glyph area. |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| trail | "short" | "normal" | "long"  (optional, default "normal") |
| scale | "fine" | "normal" | "broad"  (optional, default "normal"). Swirl size inside the letters. |
| glow | bool (optional). Soft halo behind the letters in the first colour. Default true. |

## Example payload

```json
{
  "type": "light_type"
}
```

Live page: https://a2uicatalog.ai/atoms/light_type/
Full field contract: https://a2uicatalog.ai/spec.json
