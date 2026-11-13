# Quiz Set

Multi-question quiz with multiple-choice options, per-question explanations, pass score, and result screen

## Surfaces

google-apps-script-web, mcp-apps, android

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
| title | string (optional) |
| questions | array of {question, options: [string], correct: integer (0-based index), explanation (optional)} |
| pass_score | integer (optional, % to pass, default 70) |
| accent | string (optional, hex) |
| on_pass | object (optional, atom block shown on pass) |
| on_fail | object (optional, atom block shown on fail) |

## Example payload

```json
{
  "type": "quiz_set"
}
```

Live page: https://a2uicatalog.ai/atoms/quiz_set/
Full field contract: https://a2uicatalog.ai/spec.json
