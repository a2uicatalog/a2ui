# Hint Reveal

A "Show hint" disclosure button that expands to reveal help text. Built on the HTML details/summary element — no JavaScript required. The summary label toggles between "Show hint" and "Hide hint". Styled with a subtle left-border accent and muted background to visually separate it from body content.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| hint | string. The hint text revealed on expand. |
| label | string (optional). Button label. Default "Show hint". |
| accent | string (optional). Left-border and icon colour. Default "#6366f1". |

## Example payload

```json
{
  "type": "hint_reveal",
  "hint": 1
}
```

Live page: https://a2uicatalog.ai/atoms/hint_reveal/
Full field contract: https://a2uicatalog.ai/spec.json
