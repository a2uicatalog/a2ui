# Loading Skeleton

A placeholder UI that shows the structure of content while it's loading, indicating active data fetching.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | no visible text in the example |
| Angular | Not verified | 2026-11-13 | no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| shape | string The general shape of the content being loaded (e.g., "card", "list", "text_block"). |
| lines | integer The number of lines of text to simulate in the skeleton. |
| has_image | boolean Indicates if the skeleton should include an image placeholder. |

## Example payload

```json
{
  "type": "loading_skeleton",
  "shape": [
    {
      "type": "rect",
      "width": "100%",
      "height": "20px"
    },
    {
      "type": "rect",
      "width": "60%",
      "height": "20px"
    }
  ],
  "lines": 1,
  "has_image": true
}
```

Live page: https://a2uicatalog.ai/atoms/loading_skeleton/
Full field contract: https://a2uicatalog.ai/spec.json
