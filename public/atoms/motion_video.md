# Motion Video

A muted video on the film clock. Inside a motion_timeline a track drives its progress p from 0 to 1 and the video seeks to from + p * (to - from), so scrubbing and frame export are exact; standalone it plays muted and loops. Made for screen recordings inside motion_device, with the motion design around them. Encode with short keyframe intervals for smooth seeking.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| url | string. https URL or a /-rooted path to an mp4 or webm (no data URLs). Otherwise a placeholder shows. |
| poster | string (optional). https URL or /-rooted image path shown before the first frame. |
| from | number (optional). Seconds into the video at p = 0, 0-3600. Default 0. |
| to | number (optional). Seconds at p = 1, 0-3600. Default the end of the video. |
| ratio | "16:9" | "4:3" | "1:1" | "3:4" | "9:16" | "9:19.5" (optional, default "16:9"). 9:19.5 is a modern phone screen. |
| fit | "cover" | "contain" (optional, default "cover") |
| radius | integer (optional). Corner px, 0-60. Default 12. |
| still | bool (optional). Standalone, hold the first frame instead of playing. Default false. |
| label | string (optional, max 80). Accessible name. Default "Video". |

## Example payload

```json
{
  "type": "motion_video",
  "url": "https://example.com"
}
```

Live page: https://a2uicatalog.ai/atoms/motion_video/
Full field contract: https://a2uicatalog.ai/spec.json
