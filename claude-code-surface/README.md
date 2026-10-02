# a2ui-claude-code — the `claude-code` surface

A Claude Code plugin (a mod) that renders A2UI blocks-dialect atoms natively in
Claude Code panes, as terminal cells. Atoms that list `claude-code` in their
`surfaces.works_on` draw here; any other atom shows a
`[type: not drawn on this surface]` placeholder instead of failing.

Drawn today: `heading`, `subheading`, `body`, `badge`, `callout`, `metric_row`,
`key_takeaways`, `steps`, `table`, `code`, `progress_bar` (animated).

## What it adds

| Command / trigger | What you get |
|---|---|
| `/a2ui [file.json \| inline JSON]` | Renders a payload (`{title, blocks}`, a bare block array, or one block) in a pane. No argument shows a demo. |
| any `mcp__a2uicatalog__*` call with `payload.blocks` | The same payload also draws in the pane, so `render_surface` / `preview_url` output appears inside Claude Code. |
| `a2ui-progress <id> <percent\|done\|clear> [label]` | An animated `progress_bar` in the Jobs pane and status line, for any script. |
| a turn running past 60s, or `/a2ui-job` | The Jobs pane: elapsed time, tool calls, context added, context %, session cost, failed calls, and rate-limit windows (% used, time to reset). |
| `gate_log` option | Optional: the latest run of a JSONL run log in the status line (`gate ✓ repo-publish 15s · 2m ago`). |

## Install

From this folder: `claude --plugin-dir /path/to/a2ui/claude-code-surface`.

Put `bin/a2ui-progress` on your `PATH` for script progress.

## Script progress

```bash
a2ui-progress build 42 "Compiling atoms"
A2UI_PROGRESS_CAPTION="step 3 of 8" a2ui-progress build 60 "Compiling atoms"
a2ui-progress build done
```

Other languages can write `{"label": "...", "value": 0-100, "caption": "..."}` to
`~/.cache/a2ui-progress/<id>.json` (or `$A2UI_PROGRESS_DIR`). A bar with no
update for 2 minutes turns amber; a finished bar stays for 15 seconds.

## Develop

```bash
claude plugin validate claude-code-surface
claude plugin test claude-code-surface
```

Rendering is in `hooks/a2ui.tsx`, the pure dashboard, progress and run-log
helpers are in `hooks/jobs.ts`, and the event wiring is in `hooks/register.tsx`.
Adding an atom here means adding a `case` to `drawBlock` and `claude-code` to
that atom's `works_on` in `atoms/schema.yaml`.
