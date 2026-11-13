# Metar Feed

METAR weather for an ICAO station via aviationweather.gov. Fetches server-side on render (cached), refreshes client-side every refresh seconds. Publishes {wind, temp, qnh, raw} to the named feed. Visual atoms bind to it by name and receive updates without a page reload.

## Surfaces

google-apps-script-web, mcp-apps, android

## Renderers

| Renderer | Status | Measured | Notes |
|---|---|---|---|
| React | Not verified | 2026-11-13 | no visible text in the example |
| Lit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Angular | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| CopilotKit | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| a2ui-vue | Not verified | 2026-11-13 | blank on both sides (light 360); blank on both sides (light 480); no visible text in the example |
| Flutter | Native | 2026-11-13 |  |
| Compose | Not supported | 2026-11-13 | component type unknown to the renderer |

What draws the atom, measured per renderer: https://a2uicatalog.ai/renderers/

## Fields

| Field | Type |
|---|---|
| name | string (optional). Feed name other atoms subscribe to. Default metar. |
| station | string (optional). ICAO station code. Default LFBO. |
| refresh | integer (optional). Client refresh interval seconds. Default 60. |
| cache | integer (optional). Server-side cache TTL seconds. Default 30. |

## Example payload

```json
{
  "type": "metar_feed"
}
```

Live page: https://a2uicatalog.ai/atoms/metar_feed/
Full field contract: https://a2uicatalog.ai/spec.json
