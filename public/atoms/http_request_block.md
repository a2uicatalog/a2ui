# Http Request Block

Renders a formatted API request block displaying the HTTP method badge, URL endpoint, headers, and body.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| method | string: GET | POST | PUT | DELETE | PATCH. The HTTP verb. |
| url | string. The fully qualified or relative API endpoint route. |
| headers | object. Key-value pairs detailing required HTTP headers. |
| body | string. Optional request payload, typically stringified JSON. |

## Example payload

```json
{
  "type": "http_request_block",
  "method": "GET",
  "url": 1,
  "headers": [
    "Name",
    "Value",
    "Status"
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/http_request_block/
Full field contract: https://a2uicatalog.ai/spec.json
