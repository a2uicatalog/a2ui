# Receipt

Show your receipts: a claim printed at the top of a till receipt, then the evidence as numbered receipt lines with a source per line (linked when a URL is given), a dashed tear line, a CONFIDENCE total, a barcode derived deterministically from the claim, and a perforated bottom edge. Built for the "no unsourced stats" rule and for AG-UI-style runs where evidence arrives one tool result at a time: resend the FULL items list on every update and only the LAST line prints in (same stateless rule as agent_sketchpad). Always paper-white, so it reads as an object on any ground. Capped at 24 items.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, pdf

## Fields

| Field | Type |
|---|---|
| claim | string (required). Printed in display type at the top. |
| items | array of {text, source?, url?} (optional). Evidence lines in order; source is a short label, url must be http(s). Strings are accepted. |
| total | number (optional). Confidence 0-1 shown as the receipt total; when absent the item count is shown. |
| total_label | string (optional). Default "CONFIDENCE". |
| merchant | string (optional). Top label. Default "EVIDENCE RECEIPT". |
| issued | string (optional). Date or context line under the merchant. |
| footer | string (optional). Default "Sources listed. No unsourced stats." |
| accent | "#rrggbb" (optional). Links and total colour. Default "#4338ca". |
| print_last | bool (optional). Animate the last line printing in. Default true. |

## Example payload

```json
{
  "type": "receipt",
  "claim": 1
}
```

Live page: https://a2uicatalog.ai/atoms/receipt/
Full field contract: https://a2uicatalog.ai/spec.json
