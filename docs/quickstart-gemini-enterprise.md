# Quickstart: A2UI Catalog in Gemini Enterprise (BYO-MCP)

Connect the live MCP server to Gemini Enterprise as a data-store connector. No API key on the catalog side (the server is open — "No authentication" is a real, correct setting, not a workaround). Public preview feature on Google's side; ~10 minutes if your org policy already allows it, longer if you need an admin to flip one setting (step 0).

This is the documented, supported path. It replaces an earlier, much heavier route (deploying a full ADK agent to Vertex AI Agent Engine) that turned out to be unnecessary — BYO-MCP is Google's own marketed answer to "connect an external MCP server," and since `a2uicatalog.ai/mcp` is already live, the entire task on your side is *provisioning*, not building.

## 0. One prerequisite: the org policy has to allow custom MCP connectors

Google ships this **off** by default, project-scoped:

```
constraints/discoveryengine.managed.disableCustomMcpServerConnector
```

Check whether it's enforced on your project:

```bash
gcloud org-policies describe discoveryengine.managed.disableCustomMcpServerConnector \
  --project=YOUR_PROJECT_ID --effective
```

If `enforce: true`, an org admin needs to override it **on this project specifically** (not org-wide — the constraint exists for a real reason: it stops any project from silently wiring an arbitrary external MCP server into your corpus, a genuine data-exfiltration surface). A project-scoped override is the correct, minimal fix — you're choosing to trust *this one* server, not disabling the guardrail everywhere.

You'll know this is your blocker if `setUpDataConnector` (or the UI equivalent) fails with `FAILED_PRECONDITION` naming that exact constraint. A generic-looking 404 earlier in the process is *not* this — see Troubleshooting below.

## 1. Add the connector (console)

Gemini Enterprise console → your app → **Data** → **Add data source** → **Custom** → **MCP server**:

| Field | Value |
|---|---|
| Server URL | `https://a2uicatalog.ai/mcp` |
| Authentication | **No authentication** |
| Connector modes | Actions (tool-calling) |

Save. Gemini Enterprise pushes its own read of your server's `tools/list` into its registry at this point — see "How this actually works" below for why that direction matters.

## 2. Verify the tools registered

Console → **Agent Registry** → find `a2uicatalog` (or your chosen display name) → confirm tools are listed: `list_catalogs`, `get_catalog`, `render_surface`, `preview_url`, `make_surface_url`, `emit_deployment`, and others.

If it shows **0 tools**, see Troubleshooting — this is a known, specific failure mode with an exact cause.

## 3. Ask your agent for a render

In the Gemini Enterprise chat / Agentspace surface:

> Using the a2uicatalog MCP server, get the catalog for dashboard atoms, then give me a `preview_url` for a `stat_card` showing "1,234 Daily users, +12%".

Gemini Enterprise doesn't have a native MCP Apps host, so ask for `preview_url` (a link) rather than `render_surface` (an inline view) — the link opens the rendered atom in a browser tab.

## 4. Own your renderer

Same as every other surface: `preview_url` runs against the catalog's shared demo Apps Script instance, rate-limited by design (10 renders/week/client). Deploy your own in four commands and point subsequent calls at it:

```bash
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-schema-renderer
clasp login && clasp create --type webapp --title "My A2UI Renderer" && clasp push && clasp deploy
```

## How this actually works (worth knowing before you scale this)

**Agent Registry is push, not pull.** It does not crawl `a2uicatalog.ai/mcp`. Step 1's console action reads your server's `tools/list` response once and stores that — a declaration, not a live observation. Ship a new atom tomorrow and the registry still reports the old tool list until someone re-registers. No SSRF risk (Google never fetches an attacker-nominated URL), no silent rug-pull (the registered contract is stable and admin-reviewable) — but it does mean **the registered tool list can go stale**. If you're automating this, re-register on every catalog release rather than once and forgetting it.

**The two "registry" concepts are different products.** `Agent Gateway` (network path, enforces traffic policy) and `Agent Registry` (the tool-list declaration in step 1/2) are separate APIs — `networkservices.googleapis.com` and `agentregistry.googleapis.com` respectively. The console flow above handles both; if you're scripting registration directly against the API, don't conflate them.

## Troubleshooting

| Symptom | Real cause |
|---|---|
| Setup fails with `FAILED_PRECONDITION` naming `disableCustomMcpServerConnector` | Step 0 — org policy is blocking custom MCP connectors on this project. Needs an admin override, project-scoped. |
| A **generic-looking 404** early in setup (not the policy error above) | Almost always a wrong `dataSource`/connector-type value if you're scripting this directly against the API rather than using the console — the correct value for a custom MCP server is `custom_mcp`, which the discovery document's own enum (`REMOTE_MCP`) doesn't map to cleanly. The console flow in step 1 avoids this entirely; only relevant if you're calling `setUpDataConnector` yourself. |
| Registry shows 0 tools after registering | The registered spec type was `NO_SPEC` (no content) instead of `TOOL_SPEC` (the real `tools/list` payload). If scripting registration, this field is immutable after creation — delete and recreate with the correct type, you can't patch it in place. |
| Tools list looks stale (missing a newly-added atom/tool) | Expected — see "push, not pull" above. Re-register to refresh. |
| `render_surface` doesn't render inline | Gemini Enterprise isn't an MCP Apps host — always ask for `preview_url` here, not `render_surface`. |
