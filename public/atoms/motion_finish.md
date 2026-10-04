# Motion Finish

A finishing layer for the whole frame, like a colourist: film grain (fixed seeded noise, drifting with --s), a vignette, warm or cool light leaks that drift, and an optional glass sheen that sweeps across with p. Place it last and full size (place 0,0,100,100); it never takes clicks. p fades it in. Plain SVG and CSS, no script.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| grain | bool (optional). Film grain. Default true. |
| grain_amount | number (optional). 0-0.5. Default 0.12. |
| grain_size | "fine" | "medium" | "coarse" (optional, default "medium") |
| vignette | bool (optional). Default true. |
| vignette_amount | number (optional). 0-1. Default 0.55. |
| leak | "warm" | "cool" | false (optional, default "warm") |
| leak_amount | number (optional). 0-1. Default 0.35. |
| sheen | bool (optional). A diagonal highlight band sweeping across with p. Default false. |

## Example payload

```json
{
  "type": "motion_finish"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_finish/
Full field contract: https://a2uicatalog.ai/spec.json
