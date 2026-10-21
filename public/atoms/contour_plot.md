# Contour Plot

Filled contour bands drawn from data: either a grid of values (a temperature, elevation or pressure field) or a cloud of points (the density of delivery locations, incidents or customers). Both use d3-contour: for a grid, marching squares at evenly spaced levels (d3's default count of levels, or the thresholds field); for points, a kernel density estimate (d3 contourDensity: the points are smoothed with the given bandwidth and contoured at up to 20 levels). Bands run from light to dark as the value or density rises, every band is named in a legend as a range of numbers (never colour alone), and a thin outline marks each level. A grid is drawn with column and row numbers on its axes; points use their own x and y with nice axis ticks and are also drawn as faint dots. Static SVG, no script, scaled to its container. The hidden tables give every level with its colour name and, for a grid, the share of cells at or above it, for points the share of points in cells at or above it, then the points themselves (first 200). The aria label gives the mode, the size, the value range and the number of levels. Motion-ready: each band reads --p through a --k so a motion_timeline track on p draws the bands from the lowest level up; the standalone render is the finished picture.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| grid | object (one of grid or points is required): {width (whole number, 2 to 100), height (whole number, 2 to 100), values (array of width times height numbers, row-major: the first row is the top)}. A value that is not a finite number (or beyond 1e12) is left empty, counted in a note and treated as below every level, as d3 does. A grid whose size is not right gets a note instead of the chart. If points is also given, the grid is drawn and a note says so. |
| points | array (one of grid or points is required, 3 to 2000) of {x, y} numbers. An entry that is not an object with finite numeric x and y is skipped and counted in a note; points beyond the first 2000 are noted and not used; fewer than 3 usable points gets a note instead of the chart. The axes are the data range niced by d3 (a flat range is widened by 1 each side), y up. |
| thresholds | integer (optional, 3 to 20; another number is clamped, a fraction is rounded down). How many levels d3 aims for: ticks at 1, 2 or 5 times a power of ten, so the drawn count can differ. Default: for a grid d3's Sturges count from the number of cells (thresholdSturges); for points 20. |
| bandwidth | number (optional, 5 to 60, default 20; clamped). Points mode only: the smoothing radius of the kernel density, in pixels of the 600 by 400 drawing (it scales with the chart). Larger merges clusters. |
| x_label | string (optional, max 30). Under the plot. A grid defaults to "Column". |
| y_label | string (optional, max 30). Above the plot. A grid defaults to "Row". |
| value_label | string (optional, max 30). Grid mode only, names the values in the legend (default "Value"). Points mode names the density itself. |
| unit | string (optional, max 12). Grid mode only, appended to the values in the legend, the tables and the aria label. |
| version | integer (optional, default 1). The contour_plot contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "contour_plot",
  "grid": 1,
  "points": 1
}
```

Live page: https://a2uicatalog.ai/atoms/contour_plot/
Full field contract: https://a2uicatalog.ai/spec.json
