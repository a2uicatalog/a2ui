# Adsb Feed

OpenSky Network ADS-B live traffic feed for a geographic bounding box. Fetches server-side on render (cached), refreshes client-side every refresh seconds. Publishes normalised flight objects {callsign, lat, lon, alt_ft, spd_kt, hdg, on_ground, squawk} to the named feed. Unauthenticated OpenSky limit is 400 req/day — keep cache TTL >= 15s.

## Surfaces

google-apps-script-web

## Fields

| Field | Type |
|---|---|
| name | string (optional). Feed name other atoms subscribe to. Default adsb. |
| lat_min | number (optional). Bounding box south edge degrees. Default 43.1 (LFBO TMA). |
| lat_max | number (optional). Bounding box north edge degrees. Default 44.2. |
| lon_min | number (optional). Bounding box west edge degrees. Default 0.7. |
| lon_max | number (optional). Bounding box east edge degrees. Default 2.0. |
| refresh | integer (optional). Client refresh interval seconds. Default 15. |
| filter_ground | boolean (optional). Exclude on-ground traffic. Default true. |
| cache | integer (optional). Server-side cache TTL seconds. Default 15. |

## Example payload

```json
{
  "type": "adsb_feed"
}
```

Live page: https://a2uicatalog.ai/atoms/adsb_feed/
Full field contract: https://a2uicatalog.ai/spec.json
