# Nav Bar

Horizontal or vertical navigation bar linking to other named A2UI pages. Generates correct ?nav=<slug>&from=<current_slug> URLs at runtime using window._A2UI_NAV — no deployment URL needs to be hard-coded. Optionally sticky below the system nav header. Active page is highlighted automatically by comparing slugs.

## Surfaces

google-apps-script-web, web, google-meet-stage, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (optional). Small uppercase label above the bar. |
| layout | string (optional). "horizontal" (default) or "vertical". |
| sticky | boolean (optional). Whether to stick below the system nav header. Default true. |
| top_offset | integer (optional). Top offset in px when sticky. Default 52. |
| accent | string (optional). Active link accent colour. Default |
| links | array (required). Array of {nav_slug, label, icon?, active?} objects. nav_slug is the saved page slug; the correct URL is generated at runtime. |

## Example payload

```json
{
  "type": "nav_bar",
  "links": [
    {
      "label": "GitHub",
      "url": "https://github.com/a2uicatalog/a2ui"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/nav_bar/
Full field contract: https://a2uicatalog.ai/spec.json
