# Sunburst

Part-to-whole as nested rings: each item is an arc whose angle shows its share of the total, the top-level groups sit in the innermost ring and each level of the optional per-item path (1 to 3 group names, top down) is one ring further out, so a budget, a disk-usage breakdown or a folder tree reads from the inside out. Laid out by d3-hierarchy partition() and drawn with d3-shape arc() paths on the server, so there is no script. With the optional layout "icicle" the same hierarchy is drawn as horizontal bars instead, the top-level groups in the left column and each level one column further right. A group's hue follows its top-level group and each ring out is a lighter shade of it; every arc or bar carries its name, path, value and share in a hover title and in the hidden table (item, path, value, share of total), and the aria label gives the total, the number of groups and the largest group. Labels are drawn only where they fit and are rotated to read outward, never upside down; the centre of the ring shows the total. Motion-ready: every moving value reads --p (build progress 0 to 1, default 1) through a per-ring --k, so a motion_timeline track on p builds it ring by ring from the inside out and the standalone render is the finished picture; reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| items | array (required, 2 to 40) of {path (optional, array of 0 to 3 strings, max 20 each: the item's ancestor groups from the top down; same shape as the treemap's nested mode), name (max 24, default "Item n"), value (number above 0)}. An item without a usable path is its own arc in the innermost ring. Items with a value of 0 or less, a value that is not a finite number, or that are not an item are dropped and counted in a note; items beyond the first 40 are noted and not drawn. With fewer than 2 usable items a note replaces the chart. |
| layout | "radial" or "icicle" (optional, default "radial"). radial draws concentric rings (a sunburst); icicle draws horizontal bars with the top-level groups on the left. Any other value is drawn as radial. |
| unit | string (optional, max 12). Appended to every value in the title, the centre, the aria label and the hidden table. |
| version | integer (optional, default 1). The sunburst contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "sunburst"
}
```

Live page: https://a2uicatalog.ai/atoms/sunburst/
Full field contract: https://a2uicatalog.ai/spec.json
