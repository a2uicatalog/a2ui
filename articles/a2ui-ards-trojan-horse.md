# A2UI as the Trojan Horse: Why the Vocabulary IS the Discovery Layer

**Status:** Draft — for further exploration  
**Date:** 2026-06-20  
**Tags:** A2UI, ARDS, agentic-systems, enterprise-ai, schema-design

---

## The Problem ARDS Is Trying to Solve

Google's Agentic Resource Discovery Specification (ARDS), announced June 2026, addresses a real coordination problem: agents operating in distributed ecosystems have no standard way to discover what capabilities exist, which to use, and whether they're safe to connect to.

The ARDS answer is infrastructure: publish an `ai-catalog.json` at a well-known domain path, let registries crawl and index it, have agents query registries at runtime, verify via domain-ownership cryptography, then connect.

It's a web paradigm — elegant for open ecosystems, fragile in enterprise contexts.

---

## The Enterprise Antipattern Hidden in Plain Sight

ARDS's crawling model assumes public discoverability. But enterprise security is architecturally opposed to that premise. In a zero-trust architecture, you don't reveal what capabilities *exist* until identity and authorization are established. The capability catalog itself is sensitive information.

ARDS inverts the correct enterprise sequence:

| Model | Sequence |
|---|---|
| ARDS | Discover publicly → authenticate at connection time |
| Enterprise zero-trust | Authenticate first → discover what you're authorised to see |

This matters. An internal API's existence can be as sensitive as its data. Crawling registries over the public internet to surface internal Workspace tooling is architecturally backwards for most enterprise deployments.

---

## The A2UI Counterargument: Vocabulary as Discovery Layer

A2UI makes a different bet: **if the schema is rich enough, discovery becomes unnecessary**.

Instead of an agent discovering capabilities at runtime via external registries, A2UI compiles the entire capability surface — 400+ typed atoms, surface declarations, and connector definitions — into the agent's context before any prompt is processed. The agent doesn't discover what it can do. It already knows, because the vocabulary was compiled for it.

```
ARDS model:
  agent → registry → catalog → verify → connect → render

A2UI model:
  schema → snapshot → agent context → prompt → render
```

The snapshot is the catalog. The connector schema is the protocol definition. The surface declaration is the auth scope. All resolved at build time, not at runtime.

---

## The Connector Schema as Embedded ARDS

What makes A2UI's approach structurally coherent is the connector layer now embedded in `schema.yaml`. Each atom declares:

```yaml
- type: gmail_inbox
  surfaces:
    works_on: [google-apps-script-web, web, meet-stage]
  connectors:
  - id: gas-native
    surfaces: [google-apps-script-web]
    live: true
    description: Live data via GmailApp — no config needed
  - id: static
    surfaces: ["*"]
    live: false
    description: Render from items[] payload field
  - id: api
    surfaces: [web, meet-stage]
    live: true
    endpoint: https://gmail.googleapis.com/gmail/v1/users/me/threads
    fields:
      auth_token: OAuth2 bearer token
```

This is functionally equivalent to an ARDS capability entry — typed, surface-scoped, connector-aware, with explicit protocol endpoints. The difference: it's injected into the agent's context, not published to a public registry.

The agent (Gemini) reads the schema snapshot and knows:
- This atom works on GAS natively with zero config
- On web, pass `items[]` for static rendering
- `auth_token` unlocks the live REST API path on any surface

No crawling. No registry query. No well-known path exposure. Enterprise auth is ambient — you're the authorised user, your OAuth scopes activate the right connector automatically.

---

## The Trojan Horse Framing

A2UI enters organisations as a demo tool — "generate rich pages for Google Meet from a single prompt." But what it demonstrates at the architecture level is more disruptive:

**Agentic applications don't need discovery infrastructure if the vocabulary is well-schematised.**

The insight is that the "discovery problem" ARDS addresses only exists because most applications are built as opaque endpoints with implicit, undocumented capability surfaces. Agents can't know what they can do because nobody wrote it down in machine-readable form.

A2UI proves the alternative: a typed, surface-aware, connector-annotated schema compiled into agent context eliminates the discovery problem at source. The schema IS the contract. Build time resolution beats runtime crawling every time in enterprise contexts — it's faster, more secure, and audit-friendly.

---

## Where ARDS Still Wins

This isn't a dismissal of ARDS. There are domains where its crawling model is exactly right:

- **Public SaaS ecosystems** — Zapier-style integrations, public tool directories, cross-org agent collaboration where participants are unknown in advance
- **Open web agents** — browser-based assistants discovering tools across arbitrary domains
- **Federated discovery** — when you genuinely don't know the universe of capabilities ahead of time

ARDS will find its natural home here, and likely becomes the plumbing for how consumer AI assistants connect to third-party services. Google Workspace Admin will almost certainly become an enterprise ARDS authority — private registries with IAM-gated catalog access — as the spec matures.

---

## The Positioning Opportunity

The timing is notable. ARDS was announced June 2026 as a forward-looking spec with no production tooling. A2UI is running today, inside enterprise auth, generating surface-appropriate agentic output from a compiled vocabulary schema.

The provocative framing for a broader audience:

> *ARDS solves discovery for the open web. A2UI solves it for the enterprise — by making discovery unnecessary.*

A response piece or technical post exploring this contrast could land well given the announcement timing. The core argument is not that one approach is wrong, but that the appropriate solution depends on whether you're building for open ecosystems or authenticated enterprise surfaces — and that the compiled-vocabulary approach deserves a name and a spec of its own.

---

## Open Questions for Further Exploration

- Should A2UI publish a formal spec for "compiled vocabulary schemas" as a pattern? A named counterpart to ARDS for enterprise-native agentic apps?
- Can the `connectors` schema in `schema.yaml` be aligned more formally with ARDS capability entry format to enable interop if ARDS tooling matures?
- Is there a hybrid: private ARDS registry (behind IAM) where the catalog is the A2UI schema snapshot, served to authorised agents only?
- How does this framing interact with MCP? MCP handles tool execution; ARDS handles tool discovery; A2UI collapses both into the vocabulary layer. Is that a feature or a limitation at scale?
- What does "A2UI for enterprise" look like as a product pitch — a Schema-as-Platform play?
