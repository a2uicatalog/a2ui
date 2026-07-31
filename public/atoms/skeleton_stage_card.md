# Skeleton Stage Card

Dark-themed shimmer skeleton loader for stage use while a playbook is processing. Four variants — card (avatar + text lines), list (avatar rows), media (image header + caption), chat (alternating message bubbles). All use a CSS linear-gradient shimmer animation with no JavaScript.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| variant | string (optional). One of card, list, media, chat. Default card. |
| lines | integer (optional). Number of text lines or list rows to show. Default 3. |
| count | integer (optional). Number of skeleton cards to stack. Default 1. |

## Example payload

```json
{
  "type": "skeleton_stage_card"
}
```

Live page: https://a2uicatalog.ai/atoms/skeleton_stage_card/
Full field contract: https://a2uicatalog.ai/spec.json
