# Motion Group

Blocks that enter one after another: a stagger, set once. Every child gets the same entrance (effect, ease, duration) offset by stagger milliseconds, on load or when scrolled into view. The general-purpose alternative to hand-setting a delay on each block; for a single block use the `enter` prop that any atom accepts.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| blocks | array (max 40) of any atom blocks. |
| effect | "fade" | "rise" | "drop" | "slide-left" | "slide-right" | "scale" | "blur" | "wipe" | "pop" (optional, default "rise") |
| ease | string | [x1,y1,x2,y2] (optional). A token from motion_tokens, or four numbers. Default depends on the effect (expo-out for most). |
| duration | integer | "instant" | "quick" | "base" | "slow" | "cinematic" (optional). Milliseconds 0-8000 or a duration token. Default 560. |
| delay | integer (optional). Milliseconds before the first child, 0-20000. Default 0. |
| stagger | integer (optional). Milliseconds between children, 0-1000. Default 80. |
| on | "load" | "view" (optional, default "load"). "view" waits until the group is scrolled into view; without JavaScript it simply shows. |

## Example payload

```json
{
  "type": "motion_group",
  "blocks": [
    {
      "type": "body",
      "text": "Example content."
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/motion_group/
Full field contract: https://a2uicatalog.ai/spec.json
