# Sortable List

Drag to reorder a list, emitting the new position as one event.
A DATA atom, not a domain one: it renders whatever {id, label} pairs it is given and emits a position, so the same atom serves form fields, a shopping run, or any other AUTHORED ordering. There is deliberately no sortable_jobs and no sortable_fields — one named interaction per use case is the drift this vocabulary already has (onFlightClick, onAssign), and it costs a renderer change every time.
The reason it fits a declarative binding model at all is containment: the gesture never reaches the state engine. dragstart/dragover/drop are high-frequency and purely visual; only the DROP publishes, once, through the `onReorder` output wire as {id, order}. That is the same shape the atom renders FROM, so position is derived state rather than a second source of truth — what it emits and what it consumes are one field.
`order` is fractional: a drop takes the midpoint of its two neighbours, so exactly one item changes. Dense re-indexing would rewrite every position on every drag, turning a one-line reviewable diff into a wall of noise, which matters wherever the result is a change someone accepts or reverts.
Use it only where order is AUTHORED. Where order is COMPUTED — a job list ranked by severity then priority — a dragged position becomes a second, competing ordering, and the derivation boundary rule says that ranking belongs to the server.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| items | array (required). Objects of {id, label, order?, group?, note?}. `id` is what comes back in the event, `label` is what is shown, `order` seeds the fractional position (defaults to the array index), `group` is an opaque bucket id carried back on drop, `note` is optional right-aligned secondary text. |
| label | string (optional). A small heading above the list. |
| emptyMessage | string (optional). Shown instead of the list when items is empty. Default "Nothing to reorder." |

## Example payload

```json
{
  "type": "sortable_list"
}
```

Live page: https://a2uicatalog.ai/atoms/sortable_list/
Full field contract: https://a2uicatalog.ai/spec.json
