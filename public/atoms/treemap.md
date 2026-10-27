# Treemap

Part-to-whole as nested rectangles whose areas show share of the total, laid out by the squarified treemap algorithm (d3-hierarchy treemapSquarify). By default up to four categories: each category is one block and its items are rectangles inside it, with the category name and total in a pill. With an optional per-item path (1 to 3 group names, top down) the chart nests by that path instead, up to three levels of group boxes with a header showing the group name and total, so a folder tree or a cost breakdown reads like a disk-usage map. Each rectangle carries its name and value where the drawn width and height can hold them; in a narrower container or a thin cell the label is hidden (the hover title and the hidden table keep it). A hidden table gives item, category (or path), value and share. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-item --k, so a motion_timeline track on p builds it item by item and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| items | array (required, 4 to 12) of {category (max 20), name (max 24), value (number above 0), path? (array of 1 to 3 strings, max 20 each, the item's ancestor groups from the top down)}. Without any path at most four categories are drawn; items with a value of 0 or less are dropped. When any item has a usable path the chart nests by path and category is ignored for items that have one; an item without a path goes into a group named by its category, or Other. The item cap is 12 unless max_items is given. |
| max_items | integer (optional, 12 to 60, default 12). Lifts the item cap; items beyond it are not drawn and a note says how many. Any other value keeps 12. |
| version | integer (optional, default 1). The treemap contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "treemap",
  "items": 1
}
```

Live page: https://a2uicatalog.ai/atoms/treemap/
Full field contract: https://a2uicatalog.ai/spec.json
