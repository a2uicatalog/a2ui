# Form Textarea

Multi-line text input. Wire onChange to a ValueStore setValue to capture typed content.

## Surfaces

web, google-apps-script-web, mcp-apps, android

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
| label | string (optional) |
| placeholder | string (optional). Greyed-out hint text, NOT a real value — never submitted if the reader doesn't type. Use `value` instead for a real, editable, submittable pre-fill. |
| value | string (optional). Real pre-filled, editable content — rendered as actual text inside the box, submitted as-is if the reader doesn't change it. If you also declare a ValueStore for this field's onChange, keep its initialValue equal to this same string, or a reader who never touches the box will submit an empty value despite seeing real text. |
| rows | integer (optional, default 4) |

## Example payload

```json
{
  "type": "form_textarea"
}
```

Live page: https://a2uicatalog.ai/atoms/form_textarea/
Full field contract: https://a2uicatalog.ai/spec.json
