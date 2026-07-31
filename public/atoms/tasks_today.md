# Tasks Today

Incomplete tasks displayed as an interactive checkbox list. On GAS uses the Tasks API for live data; on other surfaces renders from an items[] array or the Google Tasks REST API.

## Surfaces

google-apps-script-web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional). Card heading. Default is "Today's Tasks". |
| max_results | integer (optional). Maximum tasks to show. Default 10. |
| list_name | string (optional, gas-native). Name of the task list. |
| items | array (static connector). Array of {title, due, completed} for non-GAS surfaces. |
| auth_token | string (api connector). OAuth2 bearer token for REST API. |

## Example payload

```json
{
  "type": "tasks_today",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ],
  "auth_token": "your-api-token"
}
```

Live page: https://a2uicatalog.ai/atoms/tasks_today/
Full field contract: https://a2uicatalog.ai/spec.json
