# Choropleth Map

A map of regions shaded by one number each: world countries, US states or European countries. Give a region_set and a list of {id, value}; the server shades every region in one of 3 to 9 equal-interval classes (steps, default 5), draws a legend of the class ranges and hatches the regions that have no value, so a gap never reads as a low number. Colours come from the theme tokens (sequential accent ramp, or a diverging accent2-to-accent ramp through a neutral middle); Viridis, Turbo and other fixed colour maps are not offered. The outlines are bundled with the catalogue (Natural Earth 1:110m for countries, US Census 1:10m for states): there is no custom GeoJSON, so a region that is not in the set cannot be added. A hidden table lists each region with its code, value and class, largest first, and the regions with no value are listed in a details element. A payload that breaks the rules shows a short note instead of a map.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| version | integer (optional, default 1). Payload contract version. |
| title | string (optional, max 80). Shown above the map and used as its name. |
| region_set | string (required): world-countries (176 countries, Antarctica left out), us-states (the 50 states and DC) or europe-countries (the European subset of world-countries, Russia and Turkey included, framed on the area west of 45 degrees east). Use it to choose which outlines are drawn; the set also decides which ids are valid. |
| projection | string (optional): equal-earth, mercator or albers-usa. Equal Earth keeps areas comparable, so it is the default for world-countries and europe-countries; Mercator suits a close view of Europe but inflates high latitudes; albers-usa (the d3 composite that moves Alaska and Hawaii under the lower 48) is only valid with us-states and is its default. Any other combination, or any other name, shows a note. Use this to change the look, not the data. |
| values | array (required, 1 to 250) of {id (string), value (number)}. id is an ISO 3166-1 alpha-3 code for the country sets (for example FRA; Kosovo is XKX) or a 2-letter USPS code for us-states (for example TX; DC is included); case is ignored. value is a finite number of at most 1e15 in size. Entries beyond the 250th are ignored, an unknown id is skipped and named in a note, a repeated id keeps its first value, and an entry without a usable id and number is counted in a note; if nothing matches a region the map is not drawn. |
| scale | object (optional) {kind, scheme?}, the scale contract of chart_legend without the domain (the domain is the data). kind is sequential (default: low to high, one direction) or diverging (a neutral middle, two directions, for values that rise and fall around a centre such as change or difference). scheme is a theme-token ramp name: accent (default) or accent2 for sequential, accent_pair for diverging; any other name falls back to the default. For diverging the centre is 0 when the values cross zero, otherwise the middle of the range. Use diverging only when the centre means something. |
| unit | string (optional, max 12). Appended to the legend ranges and the table values (for example % or USD), with no space before a percent sign. |
| legend_title | string (optional, max 60). A heading for the legend (for example Unemployment rate, %); the map title says what the map is, the legend title says what the colours measure. |
| steps | integer (optional, 3 to 9, default 5). The number of classes. Fewer classes read faster and hide detail; more show detail but neighbouring shades get hard to tell apart. A number outside 3 to 9 is moved to the nearest and named in a note. |
| frame | object (optional) {lon_min, lon_max, lat_min, lat_max}, four finite numbers in degrees: frame the map on a zone (for example a trip) instead of the whole region_set. Longitude is clamped to -180..180 and latitude to -85..85, lat_min must be below lat_max after that, and a span under 1 degree is widened to 1. lon_min above lon_max is a frame across the antimeridian (160 to -150 is a Pacific trip: Fiji, Samoa, Hawaii): the map is drawn with its central meridian at the frame's centre, so outlines, points and routes run on across 180 as one piece; a frame that reaches -180 or 180 is centred the same way, so the land past the seam is drawn. lon_min equal to lon_max is not a frame. A motion_transition between two frames on either side of the seam pans and zooms each keyed region's box (a region drawn in two pieces across the seam travels as one box). A frame that contains no outline of the set is named in a note. A framed map has a sea tint (a mix of theme tokens; left out when the frame reaches past the region set's window, where the set has no land) and rounded corners. The frame is fitted into a fixed 960 x 540 canvas and centred, so two states of one film with different frames have the same box and a motion_transition between them pans and zooms: regions keep their data-key. Outlines outside the frame are drawn and cropped by the viewBox, not dropped. Not used with albers-usa (a fixed composite). A frame that cannot be used is named in a note and the whole map is drawn. Absent: unchanged. |
| categories | array (optional, 1 to 6 names, text up to 40) of category names: switches the map to category mode. Each value is then a category name instead of a number ({id, value: "visited"}); the scale, steps and unit are not used. Each category gets a colour AND a pattern (dots, horizontal stripes, vertical stripes, cross-hatch, backslash stripes, large dots, in list order), so colour is never the only cue; regions with no category are hatched on the surface colour (forward slash) and listed in a details element. The legend lists the categories (data-key class-1 to class-n) and the hidden table lists region, code and category. An entry that names a category not in the list is skipped and counted in a note. |
| category_colors | object (optional) mapping a category name to a theme token name: accent, accent2, text or muted (nothing else, so the map follows the theme in light and dark). A category without an entry, or with another name, takes the default palette by position (accent, accent2, then lighter mixes of them, text and muted) and is named in a note when the name was not a token. Only used with categories. |

## Example payload

```json
{
  "type": "choropleth_map",
  "region_set": "Region set",
  "values": 1
}
```

Live page: https://a2uicatalog.ai/atoms/choropleth_map/
Full field contract: https://a2uicatalog.ai/spec.json
