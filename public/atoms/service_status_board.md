# Service Status Board

Verdict-first service status board — a lead line naming the single most important thing (all-clear, or the one active disruption), followed by a two-column grid of every tracked service with its state encoded as shape + label + color (never color alone). Designed for any status feed (Google Workspace, an internal fleet, ServiceNow) reduced to name + state.

## Surfaces

google-chat-chromium-render

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'GOOGLE WORKSPACE — SERVICE STATUS') |
| stamp | string (optional, e.g., '19 JUL 2026 · 17:45 CET'). Right-aligned timestamp. |
| verdict | dict: {level: one of ok|warn|crit, text: string headline, detail: string (optional) supporting line} |
| services | list of dicts: [{name: string, state: one of operational|disruption|information|critical}, ...] |

## Example payload

```json
{
  "type": "service_status_board",
  "services": []
}
```

Live page: https://a2uicatalog.ai/atoms/service_status_board/
Full field contract: https://a2uicatalog.ai/spec.json
