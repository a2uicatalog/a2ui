# Motion Counter

A big number that counts from `from` to `to` as p goes 0 to 1, with thousands separators, prefix, suffix, fixed decimals and an optional small-caps caption under it. The generic form of a stat for any topic: nights, artists, kilometres, followers. Plain HTML and CSS, no script: it moves with the --p custom property that a motion_timeline p track sets, and standalone it renders its final state.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| to | number (optional). Value at p = 1. Default 100. |
| from | number (optional). Value at p = 0. Default 0. |
| decimals | integer (optional). 0-3. Default 0. |
| prefix | string (optional, max 4). |
| suffix | string (optional, max 8). |
| label | string (optional, max 40). Caption. |
| label_size | integer (optional). Caption px, 8-80. Default a fifth of size. |
| size | integer (optional). Number size px, 10-400. Default 96. |
| font | "sans" | "serif" | "mono" | "display" (optional, default "display") |
| weight | "regular" | "bold" | "black" (optional, default "black") |
| color | "#rrggbb" (optional). Default the stage ink. |
| align | "start" | "middle" | "end" (optional, default "start") |
| roll | bool (optional). Odometer: every digit is a 0-9 strip that scrolls to its value, left to right, as p goes 0 to 1. Counts from zero (from is ignored). Default false. |

## Example payload

```json
{
  "type": "motion_counter"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_counter/
Full field contract: https://a2uicatalog.ai/spec.json
