# Theme Toggle

Floating light/dark theme switch persisted per visitor.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| initial | string (optional). "dark" or "light" — which state the toggle (and its label/chrome) paints as on first load. Not itself persistence — a surface that repaints itself (e.g. via paint_result) must pass the reader's LAST choice back in here, or every repaint resets to whatever this says. |
| position | string (optional, default "bottom-right") |
| dark_bg | string (optional, hex, default "#0f172a") |
| label_dark | string (optional, default "🌙") |
| label_light | string (optional, default "☀️") |
| persist_to | string (optional). A ValueStore primitive's id — when set together with persist_action, a click ALSO calls the engine directly (bypassing the standard wire-prop system, which has no event carrying "which theme it became") to set this ValueStore to "dark"/"light" and run persist_action. Omit either and the toggle is purely visual, as before. |
| persist_action | string (optional). An action id to run right after persist_to is set — typically one that saves it server-side. See persist_to. |

## Example payload

```json
{
  "type": "theme_toggle"
}
```

Live page: https://a2uicatalog.ai/atoms/theme_toggle/
Full field contract: https://a2uicatalog.ai/spec.json
