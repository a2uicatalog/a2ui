# Model Card

AI model specification card showing model name, provider, context window, pricing tier, and a row of capability badges. First-class atom for AI-native content and agent documentation.

## Surfaces

web, google-meet-stage, google-chat, email, pdf, google-apps-script-web, mcp-apps, android, slides, pptx

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
| name | string. Model display name, e.g. "Claude Sonnet 4.6". |
| provider | string (optional). Provider name, e.g. "Anthropic". |
| context_window | string (optional). e.g. "200 k tokens". |
| pricing | string (optional). e.g. "$3 / M tokens in". |
| capabilities | {'type': 'array', 'description': 'List of short capability badge strings, e.g. ["tool use", "vision", "streaming"].'} |
| accent | string (optional, default #7c3aed). Accent colour for provider label and badges. |

## Example payload

```json
{
  "type": "model_card",
  "name": "Model Card",
  "capabilities": [
    {
      "label": "Vision",
      "supported": true
    },
    {
      "label": "Code execution",
      "supported": true
    },
    {
      "label": "Web search",
      "supported": false
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/model_card/
Full field contract: https://a2uicatalog.ai/spec.json
