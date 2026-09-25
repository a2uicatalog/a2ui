# Filterable List

A list of items, each with a title, an optional detail line and a status or category, above a row of chips (All plus one per status, with counts) that actually filter it. Tapping a chip shows only the matching rows and updates the "Showing X of Y" count. Self-contained, so it works without any other atom; on a static surface it degrades to the full list.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| title | string (optional, heading above the list) |
| items | array (required). Array of {title (or name), detail? (or subtitle), status? (or whichever field filter_field names), meta? (right-aligned small text), icon? (an emoji)}. Items with no value for the filter field show only under All. |
| filter_field | string (optional, default "status"). Which item field the chips filter on, e.g. "category" or "assignee". |
| filters | array (optional). Chips to show, as plain strings or {value, label?, color? (hex)}. Default: one chip per distinct value, in first-seen order. |
| colors | object (optional). Map from a status or category value to a hex colour for its chip and row badge. Default: a distinct colour per chip. |
| show_counts | bool (optional, default true). Show how many rows each chip matches. |
| empty_text | string (optional, shown when a filter matches nothing) |

## Example payload

```json
{
  "type": "filterable_list",
  "items": [
    {
      "label": "Item 1"
    },
    {
      "label": "Item 2"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/filterable_list/
Full field contract: https://a2uicatalog.ai/spec.json
