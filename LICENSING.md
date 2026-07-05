# Licensing

**Everything in this repository is MIT-licensed** — see [LICENSE](LICENSE). That
covers the atom vocabulary (`atoms/schema.yaml`), the specs (`spec/`), the
authoring prompts (`prompts/`), the published retrieval artifacts (`public/`),
the renderers (`renderers/`, including the A2UI v1.0 emitters), and the Apps
Script reference renderer (`apps-script-surface/gas-wired-renderer`). Use it,
fork it, build on it.

## What is deliberately *not* in this repository

a2uicatalog follows an **open-core** model. The open line is drawn at the
client/server derivation boundary: everything a single user runs locally against
their own resources is open; the durable, **governed**, multi-user substrate is
commercial. Specifically not published here:

- **The MCP deploy server** (`build_app` — agent → live Apps Script app). Held
  closed for the current release; a free tier is available — see a2uicatalog.ai.
- **The hosted control plane** — auth, entitlement, tenant isolation, gated
  write-back, audit capture for multi-user deployments.
- **The managed data plane** — hosted durable stores, `store_derive` at scale,
  retention, and the audit/glass-box tier as a service.
- **Premium vertical packs** — curated domain atom + logic bundles.

Commercial components, where source-available, are released under **BSL 1.1**
(free to use and self-host; not to offer as a competing service; converts to MIT
after the change date). Contact: see a2uicatalog.ai.

Nothing in this split limits the MIT grant above: what is in this repo is yours
under MIT, unconditionally.
