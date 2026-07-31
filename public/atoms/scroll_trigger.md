# Scroll Trigger

Content that animates in from a direction when scrolled into view — alias for reveal_on_scroll

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string (alias: content) |
| title | string (optional) |
| delay | number (optional, seconds) |
| direction | string (optional, up|down|left|right) |

## Example payload

```json
{
  "type": "scroll_trigger",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/scroll_trigger/
Full field contract: https://a2uicatalog.ai/spec.json
