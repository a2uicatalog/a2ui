# Deprecation Notice

Displays a prominent warning banner indicating a feature or API is no longer supported.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| alternative | string. Recommended migration path or replacement feature. |
| removal_version | string. Optional version when the feature will be removed. |

## Example payload

```json
{
  "type": "deprecation_notice",
  "alternative": "new_component"
}
```

Live page: https://a2uicatalog.ai/atoms/deprecation_notice/
Full field contract: https://a2uicatalog.ai/spec.json
