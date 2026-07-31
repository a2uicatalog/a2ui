# Release Notes

Displays a grouped publication document containing categorised changes for a version launch.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string. Header name for the release notice. |
| added | array. Optional new features added in this release. |
| fixed | array. Optional bugs resolved in this release. |
| changed | array. Optional modifications to existing behaviour. |

## Example payload

```json
{
  "type": "release_notes",
  "title": "Release Notes"
}
```

Live page: https://a2uicatalog.ai/atoms/release_notes/
Full field contract: https://a2uicatalog.ai/spec.json
