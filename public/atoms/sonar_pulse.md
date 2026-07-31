# Sonar Pulse

A visual attention primitive that emits three concentric ring pulses outward from a centre point using staggered CSS @keyframes. Each ring animates independently with a 1-second delay offset, creating a continuous sonar effect. Four named variants map to semantic colours. No JavaScript required.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| variant | "critical" | "success" | "info" | "warning"  (optional, default "critical") |
| active | bool (optional). If false renders as a static dot. Default true. |
| label | string (optional). Short text label centred in the pulse ring. |
| size | "sm" | "md" | "lg"  (optional, default "md"). Controls ring diameter. |
| body | string (optional). Caption text below the pulse ring. |

## Example payload

```json
{
  "type": "sonar_pulse"
}
```

Live page: https://a2uicatalog.ai/atoms/sonar_pulse/
Full field contract: https://a2uicatalog.ai/spec.json
