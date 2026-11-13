# Match Exercise

Click-to-pair matching exercise. Two columns of items are shown — left (terms) and right (definitions). Learner clicks a term then a definition to form a pair. Matched pairs lock and highlight green; a mismatch briefly flashes red then resets. A score chip shows pairs matched / total. Driven by a minimal inline script.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Drawn | 2026-11-13 |  |
| Lit | Drawn | 2026-11-13 | seeded-random order differs per renderer: pixel and text parity with React are excluded for this atom, not counted as a failure |
| Angular | Drawn | 2026-11-13 | seeded-random order differs per renderer: pixel and text parity with React are excluded for this atom, not counted as a failure |
| CopilotKit | Drawn | 2026-11-13 |  |
| a2ui-vue | Drawn | 2026-11-13 | seeded-random order differs per renderer: pixel and text parity with React are excluded for this atom, not counted as a failure |
| Flutter | Native | 2026-11-13 |  |
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| pairs | list[{term: string, definition: string}]. 3 to 8 pairs recommended. |
| shuffle | boolean (optional, default true). Randomise right-column order on render. |

## Example payload

```json
{
  "type": "match_exercise",
  "pairs": [
    {
      "key": "API_KEY",
      "value": "your-key"
    },
    {
      "key": "ENV",
      "value": "production"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/match_exercise/
Full field contract: https://a2uicatalog.ai/spec.json
