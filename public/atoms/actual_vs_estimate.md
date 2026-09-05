# Actual Vs Estimate

A quantity carrying BOTH what is known and what is projected, each labelled, neither omittable. A data atom rather than a domain one: cost is only the first instance. The same shape holds for effort (hours worked vs hours estimated), for work items (closed vs open) and for anything else an app tracks with an actual alongside a forecast — which is most things worth tracking.
Exists because that distinction is where composed answers go wrong. Asked "what has this cost", a model resolves the ambiguity by guessing, and on 2026-08-14 presented a EUR300 estimate for unstarted work under the heading "COST". Selection prose can ask it not to; a required-field shape makes it unrepresentable. Both figures are mandatory for exactly that reason.
The contract runs in two directions, which is the point. Upward it constrains what a UI can say. Downward it tells the data layer what it must be able to produce: an app that cannot separate incurred from projected cannot fill this atom, and discovering that is the useful part.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| label | string (required). What the quantity IS — "Cost", "Effort", "Jobs". |
| actual | number (required). The known value, UNFORMATTED. Money spent, hours worked, items closed. |
| estimate | number (required). The projected value. Never fold this into `actual`; that is the error the atom exists to prevent. |
| unit | string (optional). Prefixed if it is a currency symbol ("EUR", "$"), suffixed otherwise (" hours", " jobs"). The renderer formats; the author supplies numbers. |
| show_total | boolean (optional, default true). The renderer DERIVES actual + estimate — the author never supplies it. A one-payload, one-render arithmetic belongs to the renderer under the derivation boundary rule, and an author who supplies a sum can supply a wrong one. Set false where adding the two is nonsense. |
| actual_label | string (optional). Overrides "Actual", e.g. "Spent so far". |
| estimate_label | string (optional). Overrides "Estimated", e.g. "Still to come". |
| total_label | string (optional). Overrides "Committed". |
| caption | string (optional). One honest sentence, e.g. "Nothing has been spent yet; EUR340 of work is planned." |
| accent | string (optional). Hex colour for the total. |

## Example payload

```json
{
  "type": "actual_vs_estimate",
  "label": "Actual Vs Estimate",
  "actual": 1,
  "estimate": 1
}
```

Live page: https://a2uicatalog.ai/atoms/actual_vs_estimate/
Full field contract: https://a2uicatalog.ai/spec.json
