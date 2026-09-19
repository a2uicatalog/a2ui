# Type Scale

A modular type scale, computed and shown as a specimen sheet. Declare a base size and a musical ratio (minor second through golden ratio) and the atom calculates every step -- px and rem to the hundredth, computed with the same integer-safe arithmetic on every renderer -- and sets the sample line at each size with a proportion bar, plus a ready-to-paste block of CSS custom properties. Calcs baked in, the way wall_elevation bakes in wall maths: an agent declares intent (base, ratio, steps), the atom does the typography. Light or dark, no JavaScript.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| base | integer (optional). Base size in px, clamped 10-32. Default 16. |
| ratio | "minor_second" | "major_second" | "minor_third" | "major_third" | "perfect_fourth" | "augmented_fourth" | "perfect_fifth" | "golden"  (optional, default "major_third") |
| steps_up | integer (optional). Steps above the base, clamped 1-8. Default 6. |
| steps_down | integer (optional). Steps below the base, clamped 0-3. Default 2. |
| sample | string (optional). Sample line set at each size. Default "The quick brown fox". |
| voice | "display" | "serif" | "mono"  (optional, default "display") |
| theme | "dark" | "light"  (optional, default "light") |
| accent | "#rrggbb" (optional). Default "#0e7bb8". |
| show_code | bool (optional). Append the CSS custom properties block. Default true. |

## Example payload

```json
{
  "type": "type_scale"
}
```

Live page: https://a2uicatalog.ai/atoms/type_scale/
Full field contract: https://a2uicatalog.ai/spec.json
