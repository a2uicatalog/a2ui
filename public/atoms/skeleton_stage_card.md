# Skeleton Stage Card

Dark-themed shimmer skeleton loader for stage use while a playbook is processing. Four variants — card (avatar + text lines), list (avatar rows), media (image header + caption), chat (alternating message bubbles). All use a CSS linear-gradient shimmer animation with no JavaScript.

## Surfaces

web, google-meet-stage, google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | no visible text in the example |
| Angular | Not verified | 2026-11-13 | no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

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
