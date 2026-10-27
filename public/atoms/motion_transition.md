# Motion Transition

Morphs one atom into another on the film's progress dial p, joining their elements by data key: two views of the same data (a treemap and a sunburst, a table and an org chart) hand over element by element instead of cross-fading. Each element of the second block that shares a key with the first starts on its partner's box and travels to its own place; with path keys a total starts on the union of its parts (Cloud collects Cloud/VMs and Cloud/Storage) and a part starts on its total; elements only in one block fade. Labels only fade. With reduced motion, on static surfaces or when no timeline sets p, the page shows the second block exactly as it renders alone.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| from | object (optional). The block shown at p = 0 (any atom). Its elements that carry the build contract (data-cb with data-key) are the start positions; it fades out over the first part of p. Missing: every element of to enters. |
| to | object (required unless patch is given). The block shown at p = 1 (any atom): the page is exactly this block when p is 1, with reduced motion, and on surfaces without script. |
| patch | array (optional) of RFC 6902 JSON Patch operations (add, remove, replace, move, copy, test) applied to a copy of from to make the p = 1 block, in place of to. Use it when the change is a few edits to the same atom (add a person to an org chart, move a card between columns): a copied item grows out of its source, a replaced id continues from the old element, a moved item keeps its key. Needs from; if to is also given, to wins. Up to 500 operations are applied. A patch that fails (bad path, failed test op) shows the from block, with an HTML comment naming the error. |
| match | "path" | "exact" (optional, default path). exact joins identical keys only. path also joins along category paths: a key that is the prefix of others (Cloud, of Cloud/VMs) starts on the union of their boxes, and a key under another (Cloud/VMs, under Cloud) starts on its parent's box. |
| key_map | object (optional, up to 200 pairs). Renames keys of from before the join, from-key to to-key, for two atoms that name the same things differently (a team table keyed by employee id to an org chart keyed by name). |
| version | integer (optional, default 1). Contract version. |

## Example payload

```json
{
  "type": "motion_transition",
  "to": "end-node"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_transition/
Full field contract: https://a2uicatalog.ai/spec.json
