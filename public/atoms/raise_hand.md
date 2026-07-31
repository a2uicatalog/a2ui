# Raise Hand

Audience raise-hand button with live count — optional Google Sheets backend

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| question | string (optional, prompt text above button) |
| label | string (optional, button label, default ✋ Raise hand) |
| write_url | string (optional, GAS doGet URL to record hands) |
| sheet_url | string (optional, Google Sheet CSV for live count) |
| poll | number (optional, poll interval ms) |
| accent | string (optional, hex) |

## Example payload

```json
{
  "type": "raise_hand"
}
```

Live page: https://a2uicatalog.ai/atoms/raise_hand/
Full field contract: https://a2uicatalog.ai/spec.json
