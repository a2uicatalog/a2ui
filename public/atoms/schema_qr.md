# Schema Qr

Self-contained QR code for a given URL (or the current page URL on JS-capable surfaces) — computed via the vendored QR-Code-generator library (Project Nayuki, MIT) and rendered as inline SVG, zero network calls. Optionally interactive — set is_interactive to add a text input that live-regenerates the QR client-side as the visitor types.

## Surfaces

web, google-meet-stage, email, pdf, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| url | string (optional, fixed URL — defaults to the current page URL on JS-capable surfaces; static surfaces render nothing if omitted) |
| label | string (optional) |
| sub | string (optional, sub-label below QR) |
| size | number (optional, px, default 220) |
| is_interactive | boolean (optional, default false). Adds a text input that live-regenerates the QR client-side. Only meaningful on web, google-apps-script-web, and mcp-apps — see degraded_on. |

## Example payload

```json
{
  "type": "schema_qr"
}
```

Live page: https://a2uicatalog.ai/atoms/schema_qr/
Full field contract: https://a2uicatalog.ai/spec.json
