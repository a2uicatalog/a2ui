# Waterfall

A running total built step by step, as horizontal bars on one shared axis: each change runs from where the previous step ended (green up, red down) and a total runs from 0 to the running total; dashed connectors join the steps and the signed change is printed at the end of each row, so the direction never rests on colour alone. The axis comes from d3 nice() and ticks(), computed on the server, so there is no script. A hidden table gives each change and the running total. Motion-ready: each step fades in through --k from --p (build progress 0 to 1, default 1); the standalone render is the finished picture and reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| steps | array (required, 1 to 24) of {label (string, max 30, default "Step n"), value (number), kind (optional, "total" or "delta", default "delta")}. A delta step needs a finite value up to 1e12 in size; a total step without a value shows the running total, and with a value sets the running total to it (a note says when that differs from the steps before it). Other entries are left out with a note; steps beyond the first 24 are noted and not drawn. Any kind other than "total" is a delta. |
| x_label | string (optional, max 40). Names the values on the axis. |
| unit | string (optional, max 12). Appended to the axis caption, the label and every value in the hidden table. |
| version | integer (optional, default 1). The waterfall contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "waterfall"
}
```

Live page: https://a2uicatalog.ai/atoms/waterfall/
Full field contract: https://a2uicatalog.ai/spec.json
