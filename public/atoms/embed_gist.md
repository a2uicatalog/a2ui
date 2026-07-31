# Embed Gist

Displays an inline styled snippet view of remote code from GitHub Gists.

## Surfaces

web, mcp-apps

## Fields

| Field | Type |
|---|---|
| gist_id | string. Hexadecimal identifier for target file fragments. |

## Example payload

```json
{
  "type": "embed_gist",
  "gist_id": "Gist id"
}
```

Live page: https://a2uicatalog.ai/atoms/embed_gist/
Full field contract: https://a2uicatalog.ai/spec.json
