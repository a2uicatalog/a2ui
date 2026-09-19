# Drop Cap

An editorial paragraph with an initial letter set four ways: dropped (the classic, sunk across 2-4 lines), raised (standing on the baseline), boxed (reversed out of an accent block), or ornament (italic, with a hairline rule). Leading quotation marks and brackets are skipped so the real first letter is the cap. Light or dark, no JavaScript. The smallest atom in the family and the one every long read wants.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| text | string (required). The paragraph, up to 2000 characters. |
| style | "dropped" | "raised" | "boxed" | "ornament"  (optional, default "dropped") |
| lines | integer (optional). Lines the dropped cap spans, clamped 2-4. Default 3. |
| voice | "display" | "serif" | "mono"  (optional, default "serif"). Face of the initial. |
| theme | "dark" | "light"  (optional, default "light") |
| accent | "#rrggbb" (optional). Colour of the initial. Default "#0e7bb8". |

## Example payload

```json
{
  "type": "drop_cap",
  "text": "A concise description of the content."
}
```

Live page: https://a2uicatalog.ai/atoms/drop_cap/
Full field contract: https://a2uicatalog.ai/spec.json
