---
title: A2UI Atomic Catalog — Versioning & deprecation policy
description: How this API changes, how you find out, and what is guaranteed not to break under you.
canonical: https://a2uicatalog.ai/versioning.md
---

# Versioning and deprecation policy

How this API changes, how you find out, and what is guaranteed not to break under you.

## Current version

Every JSON response carries the wire-format version as a header:

```http
X-API-Version: 1
```

Version 1 is the only version. There is deliberately **no `/v1/` path prefix**: the MCP
endpoint URL (`https://a2uicatalog.ai/mcp`) lives in users' client configuration files —
in `claude_desktop_config.json`, in Gemini Enterprise connector settings, in scripts.
Moving it would break every existing integration on the day it shipped, which is exactly
what a versioning policy is supposed to prevent. Versioning is therefore carried in a
header, which is one of the two forms the relevant tooling conventions accept, and the
one that does not require anyone to re-paste a URL.

## What changes without notice

These are additive and cannot break a correct client:

- **New atoms.** The catalogue grows continuously. An atom count is never a stable
  number — read it from `spec.json` rather than hardcoding it.
- **New tools** on the MCP server.
- **New optional fields** on existing responses.
- **New optional parameters** on existing tools.
- **Prose changes** — tool descriptions, guidance text, instructions. These evolve
  deliberately as better guidance is discovered.

If your client breaks when a field is *added*, that is a bug in the client. Parse
defensively and ignore what you do not recognise.

## What counts as breaking

- Removing or renaming a tool, an endpoint, a field, or an enum value.
- Changing a field's type or meaning.
- Making an optional parameter required.
- Changing an error code's meaning.

## How you find out

A breaking change is signalled on the affected responses using the two IETF standards
for exactly this, before it happens:

```http
Deprecation: @1751328000
Sunset: Wed, 01 Oct 2025 00:00:00 GMT
Link: <https://a2uicatalog.ai/versioning.md>; rel="deprecation"
```

- **`Deprecation`** ([RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html)) — when the
  deprecation takes effect, as a structured-field date.
- **`Sunset`** ([RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html)) — when the
  endpoint is expected to stop responding.

**Minimum 90 days between `Deprecation` and `Sunset`.** Neither header appears on any
response today, because nothing is currently deprecated.

## The guarantee behind the promise

Most APIs publish a compatibility promise and rely on discipline to keep it. This one
enforces it in CI.

Every deploy of the MCP server runs a **parity gate** (`test/parity.mjs`): the new code
must answer every MCP method *identically* to whatever is currently live in production,
compared structurally rather than by byte. If any response shape differs, **the deploy
fails**. Shipping an intentional behavior change requires updating the parity suite in
the same commit — which makes the change explicit, reviewable, and deliberate rather
than accidental.

That friction is the point. The common way an API breaks its consumers is not a planned
migration; it is someone changing a response shape without noticing anyone depended on
it. That specific failure cannot reach production here.

## Demonstrated practice

The policy is not aspirational — the stronger version is already in effect for MCP Apps
view resources. Four superseded `ui://` resource URIs
(`ui://a2uicatalog/view`, `/view/2`, `/view/3`, `/view/4`) remain fully servable today,
years of versions later, and have **never** been removed. A client that cached an old
tool declaration pointing at any of them still resolves it correctly.

They are also still listed in `resources/list`, marked as superseded, rather than being
silently dropped — so a client can discover that it is on an old URI instead of
discovering it when the fetch fails.

## Stability by surface

| Surface | Stability |
|---|---|
| `POST /mcp` (JSON-RPC endpoint URL) | Stable. Will not move. |
| MCP tool names and input schemas | Stable within v1; additive changes only |
| `ui://` view resource URIs | Superseded URIs kept servable indefinitely |
| `GET /spec.json` shape | Stable within v1; content grows |
| `GET /ask`, `POST /api/compose` | Stable within v1 |
| Atom *count* | Not stable — grows. Read it, do not hardcode it. |
| Individual atom field contracts | Additive; read from `spec.json`, never guess |

## If something does break

Open an issue: <https://github.com/a2uicatalog/a2ui/issues>. A break that was not
announced through the headers above is a bug in this policy's enforcement, not an
expected cost of using the service, and will be treated that way.
