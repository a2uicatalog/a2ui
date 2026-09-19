# Changed Mind

A belief change as a typographic object: "I used to think" in muted serif italic, struck through by a line that draws itself, then "Now I think" in heavy display type landing beneath it, and an optional "since" line naming what changed it. The most honest opinion format there is, and the most shared. For an agent it records a revision after new evidence rather than pretending it always knew. Light or dark.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| before | string (required). The old belief. |
| after | string (required). The new belief. |
| since | string (optional). What changed it, e.g. "since running it against a real host". |
| voice | "display" | "serif" | "mono"  (optional, default "display"). System font stacks. |
| theme | "dark" | "light"  (optional, default "dark") |
| accent | "#rrggbb" (optional). Default "#38bdf8". |
| animate | bool (optional). Strike and land on load. Default true. |

## Example payload

```json
{
  "type": "changed_mind",
  "before": "// example code",
  "after": "// example code"
}
```

Live page: https://a2uicatalog.ai/atoms/changed_mind/
Full field contract: https://a2uicatalog.ai/spec.json
