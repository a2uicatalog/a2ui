# Quiet Link

A secondary action with no button chrome — centered, small, muted, underlined text — so a screen's ONE primary action (a full-chrome button) stays visually singular. Still a real button underneath, so the standard onClick wire every other clickable atom uses works unchanged.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string (required). |

## Example payload

```json
{
  "type": "quiet_link",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/quiet_link/
Full field contract: https://a2uicatalog.ai/spec.json
