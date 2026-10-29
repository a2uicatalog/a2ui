# Chartjs Bar

Draws a static, accessible bar chart as HTML (no script, no chart library) from labels and datasets, in grouped, stacked, relative or overlaid bars, vertical or horizontal, negative values, a linear or log value axis, d3 number formats, optional value labels and a legend. Series differ by fill pattern as well as colour, and a hidden table holds every value.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| labels | array of strings. Category labels (up to 40 drawn; the hidden table lists all). |
| datasets | array of {label, data, color}. One series each (up to 8 drawn); data is numbers, anything else is skipped with a note; color is an optional |
| mode | group (default) | stack | relative | overlay. stack adds the signed values; relative stacks positives up and negatives down separately; overlay draws every series on the baseline. |
| orientation | v (default) | h. |
| show_values | boolean. Value labels on the bars; they hide when the chart is too narrow to fit them (the table keeps every value). |
| value_format | d3-format string for the value labels, for example ',.0f' or '.1%'. Types b c o p r x X are not supported. |
| y_format | d3-format string for the axis labels (and the value labels when value_format is absent). |
| y_scale | linear (default) | log. A log axis ticks at powers of ten, leaves out numbers that are not above zero (with a note) and cannot stack. |
| y_range | array of two numbers, min then max. Fixes the value axis; bars past it are cut at the axis with a note. |
| y_ticks | integer 2 to 12 (default 5). Target tick count. |
| y_reverse | boolean. Reverse the value axis. |
| gap | number 0 to 0.8 (default 0.3). Share of each category slot left empty. |
| legend_position | top | bottom | right | none. Default top with more than one series, none otherwise. |
| version | integer (optional, default 1). Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "chartjs_bar",
  "labels": [
    "Category A",
    "Category B",
    "Category C",
    "Category D"
  ],
  "show_values": true,
  "value_format": "Value format",
  "y_format": "Y format",
  "y_range": 75,
  "y_reverse": true
}
```

Live page: https://a2uicatalog.ai/atoms/chartjs_bar/
Full field contract: https://a2uicatalog.ai/spec.json
