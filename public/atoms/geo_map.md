# Geo Map

Points and lines on a map: dots at latitude and longitude, optionally sized by a number and grouped, and great-circle lines between places, drawn over the same bundled outlines and projections as choropleth_map (world countries, US states or European countries; Equal Earth, Mercator or the US composite). Each group gets its own marker shape as well as its own colour, each line its own dash, so colour is never the only cue. A hidden table lists every point (including any that fall outside the frame, which are noted) and every line. A payload that breaks the rules shows a short note instead of a map.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| version | integer (optional, default 1). Payload contract version. |
| title | string (optional, max 80). Shown above the map and used as its name. |
| region_set | string (optional, default world-countries): world-countries, us-states or europe-countries. Chooses the outlines drawn behind the data and the area the map is framed on; there is no custom GeoJSON and no map tiles. |
| projection | string (optional): equal-earth, mercator or albers-usa. Defaults as in choropleth_map (equal-earth, or albers-usa for us-states); albers-usa is only valid with us-states and moves Alaska and Hawaii under the lower 48. Any other value shows a note. |
| points | array (optional, up to 500) of {lat, lon, id?, label?, value?, group?}. id is text (max 60), the stable key of the point for a build (data-key): without it the key is the label, then the position in the list (p0, p1, ...); a repeated key gets ~2, ~3. lat is -90 to 90 and lon -180 to 180, both finite numbers. label is text (max 40) for the tooltip and the table. value is a finite number that sets the marker size (radius grows with the square root of its place between the smallest and largest value, about 2 to 8 px on a 650 px wide map; a point without a value is the smallest). group is text (max 40); each group gets a marker shape (circle, square, diamond, triangle) and a theme colour in order of first appearance, six groups at most, later groups are shown as Other; the shape and colour pairs of all six groups differ, and points without a group get their own pair and a legend entry Ungrouped (when other points have a group). A point outside the frame (for example Tokyo on a Europe map) is not drawn and is noted. Entries past the 500th are ignored with a note. |
| lines | array (optional, up to 40) of {id?, label?, path: [{lat, lon}, ...]} with 2 to 20 points per path. id is the stable key of the line (as for a point, then the label, then l0, l1, ...). Consecutive points are joined by the great-circle arc between them (d3-geo geoInterpolate, drawn with up to 64 segments each), broken where it crosses the antimeridian so it never streaks across the map. Each line has its own dash (solid, long dash, dotted) and a theme colour. |
| unit | string (optional, max 12). Appended to the values in the legend, tooltips and table. |
| legend_title | string (optional, max 60). A heading for the legend (what the marker size measures). |
| frame | object (optional) {lon_min, lon_max, lat_min, lat_max}: frame the map on a zone (a trip) instead of the whole region_set; the same rules as the frame of choropleth_map (clamped to -180..180 and -85..85, lon_min above lon_max crosses the antimeridian, a span under 1 degree widened, a fixed 960 x 540 canvas, not used with albers-usa, a bad frame is named in a note and the whole map drawn). With a frame every outline carries data-cb "tile" and its region code as data-key, so a motion_transition between two frames moves the whole map as a pan and zoom; points and routes keep their keys and travel with it. Outlines outside the frame are cropped, not dropped; a point outside it is not drawn and is noted. Absent: unchanged. |
| regions | array (optional, up to 250) of {id, category}: shade regions by category (visited, planned, not yet). id is an ISO 3166-1 alpha-3 code (or a USPS code for us-states), category text up to 40. Shaded regions keep their data-key (the code), so they travel in a transition and a region that changes category changes colour. Each category has a colour and a pattern (see categories), listed in the legend, and the hidden table lists region, code and category. |
| categories | array (optional, 1 to 6 names) fixing the category order of regions (so the colours stay the same from one state of a film to the next); without it the categories are the names of regions in first-seen order. Only used with regions. |
| category_colors | object (optional) mapping a category name to accent, accent2, text or muted (theme tokens only); the default palette by position otherwise. Only used with regions. |

## Example payload

```json
{
  "type": "geo_map"
}
```

Live page: https://a2uicatalog.ai/atoms/geo_map/
Full field contract: https://a2uicatalog.ai/spec.json
