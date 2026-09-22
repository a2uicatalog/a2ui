# Calibration Plot

A reliability diagram plotting predicted probability against observed accuracy for one or more series, with a dashed diagonal reference line for perfect calibration and optional confidence-interval bars per point. Point radius can grow with sample size (`n`). Answers whether a model's own confidence scores are trustworthy, not just whether its answers are right.

## Surfaces

web

## Fields

| Field | Type |
|---|---|
| title | string (optional, e.g., 'Jev confidence calibration') |
| x_label | string (optional, default 'Predicted probability') |
| y_label | string (optional, default 'Observed accuracy') |
| series | list of {label: string, color: string (optional hex, auto-assigned otherwise), points: list of {predicted: number 0-1, observed: number 0-1, n: integer (optional sample size, grows point radius), ci_low: number (optional), ci_high: number (optional)}} |

## Example payload

```json
{
  "type": "calibration_plot"
}
```

Live page: https://a2uicatalog.ai/atoms/calibration_plot/
Full field contract: https://a2uicatalog.ai/spec.json
