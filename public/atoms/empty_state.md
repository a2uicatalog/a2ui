# Empty State

A UI pattern displayed when there is no data to show, often with an

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| image_url | string Optional URL for an illustrative image. |
| title | string The main title for the empty state. |
| description | string A descriptive message explaining why the state is empty. |
| action_label | string Optional text for a call to action button. |
| action_url | string Optional URL for the call to action button. |

## Example payload

```json
{
  "type": "empty_state",
  "title": "Empty State",
  "description": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/empty_state/
Full field contract: https://a2uicatalog.ai/spec.json
