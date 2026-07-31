# Geo Iso Fleet

Full-viewport tabbed showcase of all three isometric aviation animations — A321neo takeoff, Ariane 6 launch, and H160 hover — in a single atom with tab switcher. Use this for a full aviation/aerospace demo page. tab field sets which scene opens by default.

## Surfaces

google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| airline | string (optional). Airline ICAO for A321neo accent — AIB, EZY, AFR, BAW, DLH, RYR. Default AIB. |
| rocket | string (optional). ESA or CNES. Default ESA. |
| livery | string (optional). Airline ICAO for H160 livery. Default AIB. |
| tab | string (optional). Starting tab — "ac" (A321neo), "rk" (Ariane 6), "hh" (H160). Default ac. |

## Example payload

```json
{
  "type": "geo_iso_fleet"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_iso_fleet/
Full field contract: https://a2uicatalog.ai/spec.json
