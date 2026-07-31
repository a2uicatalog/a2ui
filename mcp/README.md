# a2uicatalog-mcp — build live Google Apps Script web apps from your agent

**A2UI over MCP. Author, validate, deploy — no code.**

A local MCP server that gives any MCP-capable agent (Claude Desktop, Cursor, …)
a first-class Apps Script dev loop: browse the A2UI vocabulary, validate a wired
payload, and **deploy it to a live Google Apps Script web app** — returning a URL.

It's the agent-native way to build living, stateful GAS web apps: the agent
speaks the vocabulary, the parser catches mistakes (a hallucinated atom is a
parse error, not a broken screen), and `build_app` ships it.

## Tools

| Tool | What it does |
|---|---|
| `list_atoms` | Browse the atom vocabulary (`a2ui-atoms-v1`, compact descriptions) |
| `validate_payload` | Structural validation against **both** catalogs — atoms (`a2ui-atoms-v1`) + state primitives (`a2ui-state-v1`). No execution. |
| `encode_url` | gzip+base64url a payload into a renderer `?p=` preview URL |
| `get_ui` | Serve a reference wired A2UI surface as an `EmbeddedResource` (`application/a2ui+json`) |
| **`build_app`** | **Deploy a `training.md` to YOUR Apps Script → live GAS web app URL** |

Plus MCP **Resources** (`a2ui://<name>`) exposing reference wired UIs.

## Security — BYO, local, no shared secret

This is a **local dev tool**. It deploys to **your own** Apps Script using
**your own** token, read from your environment — never bundled, never a shared
hosted server. Nothing leaves your machine except the authenticated call to your
own Build API.

- `validate_payload` / `list_atoms` / `encode_url` are pure-local (no network, no secret).
- `build_app` requires two env vars **you** set, pointing at **your** deployment.

## Install

```bash
npm install -g @a2uicatalog/mcp
```

`list_atoms` / `get_atom_schema` / `validate_payload` / `encode_url` / `get_ui`
work immediately — no setup, no account. `build_app` (deploy to your own
Apps Script) needs the two env vars below.

Add to Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "a2ui": {
      "command": "npx",
      "args": ["-y", "@a2uicatalog/mcp"],
      "env": {
        "BUILD_API_URL": "https://script.google.com/macros/s/<your-api-deployment>/exec",
        "BUILD_API_TOKEN": "<your token>"
      }
    }
  }
}
```

Set your Build API endpoint + token (from your own A2UI Apps Script deployment,
only needed for `build_app`):

```bash
export BUILD_API_URL="https://script.google.com/macros/s/<your-api-deployment>/exec"
export BUILD_API_TOKEN="<your A2UI_API_TOKEN>"   # minted via ?api_setup=1 on your deployment
```

### Developing from a checkout of this repo

```bash
cd mcp && npm install
```

Then point `claude_desktop_config.json`'s `command`/`args` at
`node /absolute/path/to/mcp/server.mjs` instead of the `npx` form above.

## The loop

1. `list_atoms` — the agent learns the vocabulary
2. compose a `training.md` (or a wired payload)
3. `validate_payload` — catch atom/wire errors before deploying
4. `build_app` — **live Apps Script URL back**

Start with the GAS surface; the same payloads render across web, Meet, email,
and PDF — portability is the expansion, not a rewrite.

## Status

v0.1.0 — first public release. GAS-first, local stdio, fully self-contained
(bundles its own catalog snapshot, no network for the read-only tools).
Catalogs: `a2ui-atoms-v1` (474 atoms) + `a2ui-state-v1` (25 primitives).
