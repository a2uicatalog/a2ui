# Modal

Modal dialog overlay with a title, configurable size, and arbitrary content children. Opened programmatically or via a trigger button. Closes on X, Escape, or backdrop click.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string. Modal heading. |
| size | string (optional). One of: sm, md, lg. Default: md. |
| children | {'type': 'array', 'description': 'Content atoms to render inside the modal body.'} |
| trigger_label | string (optional). If set, renders a button that opens the modal. |

## Example payload

```json
{
  "type": "modal",
  "title": "Modal",
  "children": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/modal/
Full field contract: https://a2uicatalog.ai/spec.json
