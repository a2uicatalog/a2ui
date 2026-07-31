# Version Badge

Displays a small visual tag showing software release or dependency version numbers.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| version | string. The semantic version number or release label to display. |
| status | string: stable | beta | alpha | rc. The lifecycle stage. |

## Example payload

```json
{
  "type": "version_badge",
  "version": 1,
  "status": "Active"
}
```

Live page: https://a2uicatalog.ai/atoms/version_badge/
Full field contract: https://a2uicatalog.ai/spec.json
