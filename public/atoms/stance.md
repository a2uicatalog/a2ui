# Stance

A claim whose typography IS its calibration. The agent states a claim and a confidence 0-1; the type sets itself from it -- weight from 300 (a hunch) to 900 (a conviction), size from 1.4rem to 3rem, tracking tightening and opacity rising with confidence -- under a thin confidence rail. Optional "because" (the reason) and "unless" (what would change the agent's mind, the line most opinion cards forget). A small slider lets the reader drag the confidence and watch the claim reset, which makes the mapping legible and honest. Same integer arithmetic on the server and in the slider script.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| claim | string (required). The claim, up to 200 characters. |
| confidence | number (optional). 0-1 (values above 1 are read as percent). Default 0.5. |
| because | string (optional). The reason, one or two sentences. |
| unless | string (optional). What would change the agent''s mind; rendered as "I would change my mind if ...". |
| voice | "display" | "serif" | "mono"  (optional, default "display"). System font stacks. |
| theme | "dark" | "light"  (optional, default "dark") |
| accent | "#rrggbb" (optional). Default "#38bdf8". |
| interactive | bool (optional). Show the try-it slider. Default true. |

## Example payload

```json
{
  "type": "stance",
  "claim": "Claim"
}
```

Live page: https://a2uicatalog.ai/atoms/stance/
Full field contract: https://a2uicatalog.ai/spec.json
