# Certification Card

Completion certificate card — earner name, course title, issuer, and date with a gradient border and trophy icon. Locked behind a requires check against progress_store; becomes visible when the course is marked complete. On GAS, earner name is derived from active session if not supplied.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 |  |
| Angular | Drawn | 2026-11-13 |  |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 |  |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| course | string (required). Course name on the certificate. |
| issuer | string (optional). Issuing organisation name. Default "A2UI Learning". |
| requires | string (optional). Module/course id that must be complete to reveal the certificate. |
| earner | string (optional). Earner display name — auto-derived from GAS session if not set. |
| date | string (optional). Completion date string. Defaults to today. |
| accent | string (optional). Gradient accent colour. Default |

## Example payload

```json
{
  "type": "certification_card",
  "course": "A2UI Fundamentals"
}
```

Live page: https://a2uicatalog.ai/atoms/certification_card/
Full field contract: https://a2uicatalog.ai/spec.json
