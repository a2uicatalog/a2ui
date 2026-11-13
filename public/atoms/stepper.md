# Stepper

Vertical step sequence where completed steps show an animated SVG checkmark draw, the active step pulses with a sonar-style glow ring, and pending steps are muted. State is driven by active_index — a single integer the agent increments as each step completes. No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| steps | list of strings or {label, description} objects. Each step in the sequence. |
| active_index | integer (optional, default 0). Index of the currently executing step. Steps before it are completed; steps after are pending. |
| color | string (optional). Accent colour for completed/active states. Default "#38bdf8". |
| label | string (optional). Heading above the step list. |

## Example payload

```json
{
  "type": "stepper",
  "steps": [
    {
      "title": "Step one",
      "body": "First thing to do."
    },
    {
      "title": "Step two",
      "body": "Then this."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/stepper/
Full field contract: https://a2uicatalog.ai/spec.json
