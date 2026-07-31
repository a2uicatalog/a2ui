# Llm Comparison Table

Side-by-side comparison of outputs from multiple language models for the same prompt — model name, output text, and optional latency/cost/token metadata per column. Designed for model evaluation, A/B testing, and capability demonstrations. Original a2ui-catalogue atom.

## Surfaces

web, google-meet-stage, pdf, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| prompt | string (optional). The shared input prompt shown above the comparison. |
| models | {'type': 'array', 'description': 'List of {name, output, latency_ms?, cost_usd?, tokens?} model result objects.'} |
| show_meta | boolean (optional). Show latency/cost/token row below each output. Default true if any model provides meta fields. |

## Example payload

```json
{
  "type": "llm_comparison_table",
  "models": [
    {
      "name": "GPT-4",
      "context": "128k"
    },
    {
      "name": "Claude Sonnet",
      "context": "200k"
    }
  ]
}
```

Live page: https://a2uicatalog.ai/atoms/llm_comparison_table/
Full field contract: https://a2uicatalog.ai/spec.json
