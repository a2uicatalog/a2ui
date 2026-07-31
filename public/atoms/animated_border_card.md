# Animated Border Card

Card with a continuously rotating gradient border, created by a spinning conic-gradient pseudo-element — no JavaScript. Two accent colours blend through the border. Inner content area has a solid background. Ideal for highlighting key facts, announcements, or featured atoms in a catalogue.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Card heading. |
| body | string. Card body content (markdown inline formatting supported). |
| accent | string (optional). Primary border gradient colour. Default "#38bdf8". |
| accent2 | string (optional). Secondary border gradient colour. Default "#818cf8". |
| background | string (optional). Inner card background colour. Default "#ffffff". |
| speed | "slow" | "normal" | "fast"  (optional, default "normal") |
| border_width | integer (optional). Border thickness in px. Default 2. |

## Example payload

```json
{
  "type": "animated_border_card",
  "body": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/animated_border_card/
Full field contract: https://a2uicatalog.ai/spec.json
