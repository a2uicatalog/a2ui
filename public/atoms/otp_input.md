# Otp Input

One-time password entry field. Renders N individual digit boxes (default 6) with filled/unfilled visual state. Shadcn InputOTP pattern.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| length | integer (optional). Number of digit boxes. Default 6. |
| value | string (optional). Pre-filled digits. |
| label | string (optional). Visible label above the boxes. |

## Example payload

```json
{
  "type": "otp_input"
}
```

Live page: https://a2uicatalog.ai/atoms/otp_input/
Full field contract: https://a2uicatalog.ai/spec.json
