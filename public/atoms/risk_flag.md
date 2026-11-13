# Risk Flag

Structured risk callout list with severity levels, description, and mitigation. For meeting prep, project status, incident reports.

## Surfaces

web, google-apps-script-web, pdf, mcp-apps, android, slides, pptx

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
| risks | array (required). Array of {level ("critical"|"high"|"medium"|"low"), title, description?, mitigation?} |

## Example payload

```json
{
  "type": "risk_flag",
  "risks": [
    {
      "label": "Scope creep",
      "severity": "high"
    },
    {
      "label": "Timeline slip",
      "severity": "medium"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/risk_flag/
Full field contract: https://a2uicatalog.ai/spec.json
