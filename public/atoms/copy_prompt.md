# Copy Prompt

Monospace copyable text block — ideal for sharing Gemini prompts or code

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
| Compose | Native | 2026-11-13 |  |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| prompt | string (text to display and copy, alias: text, content) |
| label | string (optional, header label) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "copy_prompt",
  "prompt": "Describe what you'd like to create."
}
```

Live page: https://a2uicatalog.ai/atoms/copy_prompt/
Full field contract: https://a2uicatalog.ai/spec.json
