# Polar Chart

Points and lines placed by angle and distance from a centre: each series gives a radius r and an angle theta for every point, so a compass or wind bearing, a cyclic pattern (hour of day, month) or a radar of scores per category reads as a circular chart. Angles are degrees, or categories (any text) spread evenly around the circle, which draws a radar chart. Up to 6 series are drawn as lines, markers or both, each with its own dash and marker shape so no series depends on colour alone; the optional fill "toself" shades the closed shape of a series. The radial axis starts at 0 (or the lowest negative value) and ends at a round number d3 nice() picks, with circular gridlines at d3 ticks(); an explicit r_range sets it, and a point outside the range is not drawn and is counted in a note. Angles are turned to positions by d3-shape lineRadial() maths and scaled by a d3-scale linear scale, on the server, so there is no script. A large series is thinned to evenly spaced points (the first and last of the points read are kept) with a visible note, the same cap that stands in for Plotly's WebGL scatterpolargl; a series is read up to 5000 points and a longer one says so in a note, so no point is dropped without being counted. The hidden table lists every point with a Status column (drawn, or outside the radial range and not drawn), and the aria label gives the radial range of the drawn points, the categories and each series' extent. Motion-ready: each series fades in through --k from --p (build progress 0 to 1, default 1); the standalone render is the finished picture and reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| series | array (required, 1 to 6) of {label (string, max 30, default "Series n"), r (array of numbers, radius of each point), theta (array of numbers in degrees, or strings for categories; same length as r), mode (optional, "lines", "markers" or "lines+markers"; default "lines+markers" up to 20 points, otherwise "lines"), fill (optional, "toself" shades the shape closed from the last point to the first)}. A point needs a finite radius and angle up to 1e12 in size; an entry without a partner or number is skipped and counted in a note; series beyond the first 6 are noted and not drawn. Each series draws at most 2000 divided by the number of series points: a longer one is thinned to evenly spaced points with a note. If any theta is a string, all angles are categories. |
| categories | array (optional, up to 12 strings, max 30 each). Fixes the order of the categories around the circle; categories met in the series after these are added in order of appearance, up to 12 in all (points in later ones are noted and not drawn). |
| r_range | array (optional) of two numbers [low, high], low below high. Sets the radial axis; points outside it are not drawn and are counted in a note. Absent, the axis runs from 0 (or the lowest negative radius) to a round number above the highest. |
| r_ticks | integer (optional, 2 to 8, default 4). About how many circular gridlines the radial axis aims for. |
| theta_step | integer (optional, 30 to 180, default 30). Degrees between the labelled angle spokes of a numeric chart. |
| direction | "clockwise" or "counterclockwise" (optional). Default counterclockwise for numeric angles (as Plotly draws them) and clockwise for categories. |
| rotation | number (optional, -360 to 360). Where angle 0 sits, in degrees counterclockwise from three o'clock. The default follows Plotly: 90 (due north, like a compass) when the direction is clockwise, 0 (due east) when it is counterclockwise; so an explicit "clockwise" starts at the top, which suits wind bearings. |
| unit | string (optional, max 12). Appended to the radial values in the aria label and the hidden table. |
| version | integer (optional, default 1). The polar_chart contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "polar_chart"
}
```

Live page: https://a2uicatalog.ai/atoms/polar_chart/
Full field contract: https://a2uicatalog.ai/spec.json
