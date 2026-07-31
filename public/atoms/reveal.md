# Reveal

Wraps child blocks with entrance animations triggered on load. animation choices: fade_up, fade_in, slide_left, slide_right, scale_in, stagger.

## Surfaces

web, google-meet-stage, google-apps-script-web, google-apps-script-side-panel, mcp-apps

## Fields

| Field | Type |
|---|---|
| animation | fade_up (default), fade_in, slide_left, slide_right, scale_in, stagger |
| duration | animation duration in ms (default 500) |
| delay | initial delay in ms before first block animates (default 0) |
| stagger_delay | ms between each block when animation is stagger (default 120) |
| blocks | array of child atoms to wrap |

## Example payload

```json
{
  "type": "reveal",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/reveal/
Full field contract: https://a2uicatalog.ai/spec.json
