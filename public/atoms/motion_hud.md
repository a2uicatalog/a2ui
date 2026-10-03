# Motion Hud

A heads-up display that fills its placed box: corner brackets, a timecode that counts up from 0 to `seconds` as p goes 0 to 1, a label top right and a progress bar along the bottom. The recording-viewfinder look. Plain HTML and CSS; the timecode is rewritten by the timeline clock like motion_counter.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| seconds | integer (optional). Where the timecode ends, 1-3600. Default 10. |
| label | string (optional, max 30). Top right, e.g. REC. |
| corners | bool (optional). Corner brackets. Default true. |
| bar | bool (optional). Progress bar. Default true. |
| size | integer (optional). px, 8-60. Default 14. |
| color | "#rrggbb" (optional). Default the stage ink. |
| accent | "#rrggbb" (optional). Default the stage accent. |

## Example payload

```json
{
  "type": "motion_hud"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_hud/
Full field contract: https://a2uicatalog.ai/spec.json
