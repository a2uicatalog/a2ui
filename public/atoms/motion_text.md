# Motion Text

Kinetic type. The text reveals unit by unit as p goes 0 to 1: per line, word or character (or all at once), with reveal "mask" (each unit slides up out of a clipped line, the signature designed look), "rise", "drop", "fade" or "blur". Sized in px on the stage, so the composition is identical at any width, and coloured from the stage theme unless a colour is given. Screen readers get the plain text. Standalone it renders fully revealed. Plain HTML and CSS, no script: it moves with the --p custom property that a motion_timeline p track sets, and standalone it renders its final state.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| text | string (max 4 lines of 60 characters, 160 total; lines split on \n). Default "Text". A word between asterisks (*plan*) takes the accent colour, whichever way the text reveals; two asterisks in a row are a literal one. |
| size | integer (optional). Font size px, 10-400. Default 64. |
| font | "sans" | "serif" | "mono" | "display" (optional, default "sans"). display is a heavy grotesque. |
| weight | "regular" | "bold" | "black" (optional, default "bold") |
| mode | "lines" | "words" | "chars" | "block" (optional, default "lines"). What reveals in turn. lines never wraps; more than 120 units falls back to block. |
| reveal | "mask" | "rise" | "drop" | "fade" | "blur" | "bar" (optional, default "rise"). bar wipes a coloured highlight bar in behind each unit, then the text appears on it. |
| overlap | integer (optional). How many units are mid-reveal at once, 1-8. Higher is softer. Default 3. |
| tracking | number (optional). Letter spacing in em, -0.1 to 0.5. Default -0.02. |
| line_height | number (optional). 0.8-2. Default 1.05. |
| color | "#rrggbb" (optional). Default the stage ink. |
| align | "start" | "middle" | "end" (optional, default "start") |
| uppercase | bool (optional). Default false. |
| accent | "#rrggbb" (optional). Colour of words wrapped in asterisks. Default the stage accent. |
| bar | "#rrggbb" (optional). Colour of the highlight bar for reveal "bar". Default the stage accent. |
| extrude | integer (optional). Depth in px of a solid 3D extrusion behind the type, 0-30. Default 0. |
| extrude_color | "#rrggbb" (optional). Extrusion colour. Default "#0b0b14". |
| extrude_dir | "diagonal" | "down" (optional, default "diagonal"). Which way the extrusion falls. |
| decor | "strike" | "underline" | "highlight" (optional). A line that sweeps across each unit (line, word or character) in turn as the second dial (--s) goes 0 to 1: a strike-through (the text dims), an underline, or a marker highlight behind it. With no step track it shows finished. |
| decor_color | "#rrggbb" (optional). The sweep. Default the accent. |
| karaoke | "pill" | "color" (optional). Lights each unit (use mode words) in turn as --s goes 0 to 1, as a pill behind it or a colour change: the animated caption. Nothing is lit at 0 or 1. |
| split | integer (optional). Red and cyan copies pull apart by this many px at the peak of --s and sit together at 0: the chromatic glitch. 0-60. Default 0 (off). |
| split_a | "#rrggbb" (optional). Left copy. Default a hot pink. |
| split_b | "#rrggbb" (optional). Right copy. Default cyan. |

## Example payload

```json
{
  "type": "motion_text"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_text/
Full field contract: https://a2uicatalog.ai/spec.json
