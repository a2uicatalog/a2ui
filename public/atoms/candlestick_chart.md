# Candlestick Chart

Price movement as open-high-low-close bars on a date axis, drawn on the server as static HTML with no script. With the default style "candle" each bar is a wick from low to high and a body from open to close; with style "ohlc" it is a stem with a tick to the left for the open and a tick to the right for the close. Direction never rests on colour alone: a bar that closes at or above its open is hollow (candle) or a thin bar (ohlc) in the --positive colour, one that closes lower is filled (candle) or a thick bar (ohlc) in the --negative colour, a legend says so in words, and the hidden table has a Direction column. Bars sit at their real dates (weekend gaps show as gaps), the date axis ticks and labels follow d3-scale scaleUtc and d3-time-format, and the price axis follows d3 nice() and ticks(). An optional volume panel under the price panel repeats the hollow or filled cue. A hidden table gives every value. Motion-ready: each bar fades in through --k from --p (build progress 0 to 1, default 1); the standalone render is the finished picture and reduced motion shows the end state.

## Surfaces

web, google-apps-script-web, mcp-apps, android

## Fields

| Field | Type |
|---|---|
| title | string (optional, max 80). |
| dates | array (required, up to 10000 read) of ISO date strings, read as UTC: "2024-03-05", or with a time "2024-03-05T09:30", "2024-03-05 09:30:15" or "2024-03-05T09:30:15.250Z". Years 1000 to 9000. Any other string, a time zone offset or a non-string leaves that bar out with a note. The bars are drawn in date order. |
| open | array (required) of numbers, one per date, each finite and up to 1e12 in size. |
| high | array (required) of numbers, one per date. Must be at least the open, close and low. |
| low | array (required) of numbers, one per date. Must be at most the open, close and high. |
| close | array (required) of numbers, one per date. |
| volume | array (optional) of numbers of 0 or more, one per date. Adds a volume panel; a bar without a usable volume has no volume bar and a note counts them. |
| style | string (optional, "candle" or "ohlc", default "candle"). Any other value draws candles. |
| unit | string (optional, max 12). Appended to the price values in the aria label and the hidden table. |
| y_label | string (optional, max 40). Names the price axis above the chart. |
| version | integer (optional, default 1). The candlestick_chart contract the payload was written for. Only version 1 exists; a higher whole number is drawn as version 1 with a note. |

## Example payload

```json
{
  "type": "candlestick_chart",
  "dates": [],
  "open": 1,
  "high": 1,
  "low": 1,
  "close": 1
}
```

Live page: https://a2uicatalog.ai/atoms/candlestick_chart/
Full field contract: https://a2uicatalog.ai/spec.json
