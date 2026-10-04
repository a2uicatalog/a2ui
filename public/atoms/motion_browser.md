# Motion Browser

The catalogue browser, as a shot: a search box that types its query, filter chips with a count, and a grid of cards that rise in, each holding a LIVE render of a real atom (give the atom block as the card's preview) with its name, description, surface badge and source. One card can be picked: it lifts and takes an accent outline as step goes 0 to 1. p 0 to 0.3 types the query, p 0.3 to 1 brings the cards in. Use it to show a library of components honestly, with real names, real descriptions and real renders, instead of a mock-up. Plain HTML and CSS, no script; standalone it renders the finished screen.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| query | string (optional, max 16). Typed into the search box as p goes 0 to 0.3. |
| placeholder | string (optional, max 24). Shown before typing starts. Default "Search atoms...". |
| chips | array (max 6) of string (max 24). The first is drawn active. |
| count | string (optional, max 16). For example "51 atoms". |
| cards | array (max 6) of {title (max 28), text (max 90), badge? (max 16), source? (max 20), preview? (an atom block, rendered live)}. |
| columns | integer (optional). 2-4. Default 3. |
| pick | integer (optional). Index of the card to lift and outline as step goes 0 to 1, -1 for none. Default -1. |
| size | integer (optional). Base font px, 8-40. Default 16. |
| well | "#rrggbb" (optional). Background of the preview area of each card. Real atoms are drawn for their own surfaces and some hard-code dark text, so on a dark stage give them a light well. Default none. |
| accent | "#rrggbb" (optional). Search border, active chip, picked card. Default the stage accent. |

## Example payload

```json
{
  "type": "motion_browser",
  "chips": [],
  "cards": [
    {
      "title": "Card 1",
      "body": "First card content."
    },
    {
      "title": "Card 2",
      "body": "Second card content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_browser/
Full field contract: https://a2uicatalog.ai/spec.json
