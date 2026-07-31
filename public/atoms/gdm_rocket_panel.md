# Gdm Rocket Panel

Fixed-position canvas launch animation -- an isometric rocket climbing through exhaust trail and sparks to a HUD telemetry readout. Overlays one half of the viewport (position:fixed, non-interactive). Ported from the Google Meet Stage add-on's gdm-rocket-panel component (used in the "Apps Script is now a Workspace Core Service" playbook); graduated from stage:preview after serving as the mcp-apps page's off-catalog demo content -- the catalog's intake pipeline working as designed.

## Surfaces

mcp-apps

## Fields

| Field | Type |
|---|---|
| side | string (optional, right|left, default right -- which viewport half the overlay claims) |
| layer | string (optional, back|front, default back -- back is z-index 50, front 150, matching the original component's layer variants) |
| loop | boolean (optional, default false -- false launches once and holds at apex; true restores the original's ambient relaunch loop) |

## Example payload

```json
{
  "type": "gdm_rocket_panel"
}
```

Live page: https://a2uicatalog.ai/atoms/gdm_rocket_panel/
Full field contract: https://a2uicatalog.ai/spec.json
