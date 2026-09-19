# Contrast Audit

WCAG 2.1 contrast audit with the maths baked in: for each foreground/background pair the renderer computes the relative luminance and contrast ratio, shows a live sample swatch, and badges AA (4.5:1), AA large (3:1) and AAA (7:1) as pass or fail. Failing pairs get the nearest passing colour, found by mixing the foreground toward black or white in 5% steps until it clears AA. A summary line counts the passes. For an agent composing a surface this is the difference between "looks fine" and "is readable". No JavaScript; light or dark.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| pairs | array of {fg, bg, label?} (optional). Up to 12 pairs of "#rrggbb" colours; invalid pairs are dropped. |
| fg | "#rrggbb" (optional). Single-pair shorthand when pairs is absent. |
| bg | "#rrggbb" (optional). Single-pair shorthand when pairs is absent. |
| label | string (optional). Label for the single-pair shorthand. |
| show_fix | bool (optional). Suggest the nearest passing foreground for failures. Default true. |
| theme | "dark" | "light"  (optional, default "light") |

## Example payload

```json
{
  "type": "contrast_audit"
}
```

Live page: https://a2uicatalog.ai/atoms/contrast_audit/
Full field contract: https://a2uicatalog.ai/spec.json
