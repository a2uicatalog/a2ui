# Code Diff

Unified diff view computed server-side via Python difflib. Added lines have a green left border and fade-in background; removed lines have red. Unchanged context lines are neutral. Optional line numbers, language badge, and title. No JavaScript required — diff is computed at render time, not in the browser.

## Surfaces

web, google-meet-stage, google-apps-script-side-panel, google-apps-script-web, mcp-apps

## Fields

| Field | Type |
|---|---|
| old_code | string. The original text (before state). |
| new_code | string. The updated text (after state). |
| label | string (optional). Title shown in the header bar. |
| language | string (optional). Language badge shown in header, e.g. "python", "typescript". |
| show_line_numbers | bool (optional). Show line numbers. Default true. |
| context_lines | integer (optional). Unchanged lines shown around each change. Default 3. |

## Example payload

```json
{
  "type": "code_diff",
  "old_code": "Old code",
  "new_code": "New code"
}
```

Live page: https://a2uicatalog.ai/atoms/code_diff/
Full field contract: https://a2uicatalog.ai/spec.json
