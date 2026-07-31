# Prompt Template

Displays an LLM prompt with interpolation slots highlighted in a distinct colour. Includes an optional copy-to-clipboard button. Ideal for AI documentation, tutorials, and prompt engineering articles.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| template | string. The prompt text containing {slot} placeholders. |
| accent | string (optional, default |
| copyable | boolean (optional, default true). Show copy button. |
| label | string (optional). Small label shown above the template block. |

## Example payload

```json
{
  "type": "prompt_template",
  "template": "Hello, {{name}}!"
}
```

Live page: https://a2uicatalog.ai/atoms/prompt_template/
Full field contract: https://a2uicatalog.ai/spec.json
