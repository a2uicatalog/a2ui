# Concept Rung

One depth level of a concept_ladder — a kind chip (DEPTH N or WORKED EXAMPLE), title, body copy, an optional terminal-styled code block with caption, and an optional terminal-styled takeaway line. Reads its colour tokens from the CSS custom properties an enclosing concept_ladder sets; renders with sane fallback colours standalone. Rarely authored outside concept_ladder.rungs, but is its own atom type so it can be independently addressed by ComponentId in the A2UI v1.0 ChildList wire format.

## Surfaces

web, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| badge | string (optional). Rail-node label, e.g. the depth number or "EX". Defaults to 1-based position when rendered inside concept_ladder. |
| kind | string (optional). 'depth' (default) or 'example' — example rungs get the mono/terminal chip and node styling. |
| label | string (optional). Chip text override; defaults to "DEPTH <badge>" or "WORKED EXAMPLE" by kind. |
| title | string (optional). Rung heading. Backtick spans render as inline code. |
| body | string (optional). Rung body copy — blank-line-separated paragraphs render as separate <p>s. Backtick spans render as inline code. |
| code | string (optional). Verbatim code block, terminal-styled (escaped, never interpreted). |
| code_caption | string (optional). Italic caption line under the code block. |
| takeaway | string (optional). Terminal-styled takeaway / pull-quote line. |

## Example payload

```json
{
  "type": "concept_rung"
}
```

Live page: https://a2uicatalog.ai/atoms/concept_rung/
Full field contract: https://a2uicatalog.ai/spec.json
