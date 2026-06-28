# A2UI: A Pre-Compiled UI Vocabulary for Google Workspace

*Substrates, not composites. Reuse, don't reinvent. A personal sidequest in catalogue-first agent design — trading token spend for consistency across Meet, Chat, Apps Script, and beyond.*

---

## The problem with AI-generated UI

The moment an LLM generates a user interface from scratch, you have an uncontrolled output. It works — but it will look slightly different every time. The typography shifts. The spacing is inconsistent. A dark theme gets invented and discarded. By the next conversation context, none of the prior decisions are remembered. You burn tokens reconstructing what you built last Tuesday.

There is a better way — and it comes from a discipline older than AI: design systems.

A design system gives designers a finite vocabulary of components and rules for composing them. The mental shift for AI-assisted UI is the same: stop asking the model to invent the design on each turn, and start asking it to *express intent* using a known, pre-compiled vocabulary. The model only needs to pick atoms and fill in values. The rendering happens deterministically, every time, by a purpose-built engine.

That is the principle. The **A2UI Catalogue** is a personal project built to push this idea as far as it will go inside Google Workspace — not an official protocol, not a published framework, not affiliated with any of the projects described below. Just a sidequest to find out what happens when you take the design-system thinking seriously and build it out for every surface a Workspace agent can actually reach.

---

## What is the A2UI Catalogue?

The A2UI Catalogue is a **personal atom library** paired with a **surface-aware rendering engine**, built to explore how far the vocabulary model can stretch inside Google Workspace constraints.

It defines a schema — a vocabulary of named block types, each with a known set of fields — and a renderer that turns JSON arrays of those blocks into fully-formed, styled UI on whatever surface the agent is targeting. The catalogue currently holds **289 atoms** across 13 categories, covering gradient typography, glowing statistics, interactive tabs, live Workspace data, and Vertex AI document summaries.

The workflow:

1. A Gemini or Claude agent receives a request
2. It expresses the response as a compact JSON schema — an array of typed blocks with filled-in values
3. The renderer resolves each block type to its HTML/card/markdown equivalent for the target surface
4. The output is deterministic, styled, and consistent — no matter who asked or when

The catalogue is the interesting part. The renderer is just infrastructure.

---

## The space it lives in

To understand where this sits, it helps to look at what the broader ecosystem is doing:

**CopilotKit** is a React toolkit that makes existing frontend components "copilot-aware" — the AI can read and mutate application state in real time. Powerful, but it requires a React frontend, developer ownership of the component tree, and a web deployment.

**AG-UI** is an emerging agent-UI protocol that defines how streaming agents push state updates to a frontend. It solves the real-time sync problem cleanly. Again, it assumes a web frontend exists to receive those updates.

**v0 / Vercel's AI UI tools** take a generative approach: describe a component, receive React code. Fast and impressive, but non-deterministic — each generation is a fresh invention, and the output is not reusable across agents or sessions without copy-paste.

All three of these are solving real problems for teams building custom web applications. The A2UI Catalogue is solving a different, narrower problem: **how do you get consistent, reusable, well-designed UI inside the constrained rendering environments that Google Workspace actually provides** — Meet Stage, Google Chat Card v2, Apps Script web apps — where CDN scripts, custom build pipelines, and arbitrary JS frameworks simply do not exist?

The atoms encode the design decisions permanently. The model just speaks the vocabulary.

---

## Tokenomics: why the catalogue model pays for itself

The core claim is a simple one: **A2UI makes LLMs not write UI at all.**

Every time an LLM generates a full HTML page from scratch, it spends tokens on things it has already decided before — layout structure, spacing rules, colour system, typography scale, button styles. These are not creative decisions. They are maintenance decisions, repeated on every turn, paid for in output tokens every single time.

The catalogue model separates these two concerns:

- **Creative decisions** (which atoms to use, what content to put in them) happen at prompt time
- **Rendering decisions** (how a `glowing_stat` looks, how a `dark_hero` is structured) are compiled into the renderer once and never re-spent

Benchmarked against the same 7 UI scenarios used by the OpenUI project — a table, a contact form, a dashboard, a pricing page, a chart, a product page, and a settings panel — the numbers are clear. Token counts measured with `tiktoken` (`cl100k_base`), A2UI schemas from `benchmarks/a2ui_mappings.py`, OpenUI samples fetched from the [OpenUI benchmark repository](https://github.com/thesysdev/openui):

| Scenario | A2UI | OpenUI Lang | YAML | Vercel JSON | A2UI vs OUI |
|---|---:|---:|---:|---:|---:|
| simple-table | 92 | 149 | 317 | 332 | **−38%** |
| contact-form | 209 | 287 | 753 | 860 | **−27%** |
| dashboard | 468 | 1,232 | 2,131 | 2,192 | **−62%** |
| pricing-page | 183 | 1,217 | 2,247 | 2,437 | **−85%** |
| chart-with-data | 87 | 232 | 465 | 505 | **−63%** |
| e-commerce-product | 205 | 1,172 | 2,158 | 2,399 | **−83%** |
| settings-panel | 277 | 534 | 1,076 | 1,209 | **−48%** |
| **Total / 7 scenarios** | **1,521** | **4,823** | **9,147** | **9,934** | **−68.5%** |

A2UI outputs **3.2× fewer tokens than OpenUI Lang** and **6.5× fewer than Vercel-style JSON** across these scenarios. That gap widens further when you consider what the renderer replaces: the HTML, CSS, and JS for a typical rendered page runs to ~2,400 tokens — tokens the LLM never has to output at all. For a single-atom page that number is dramatic; for a complex multi-atom page the renderer's work compounds.

![A2UI token efficiency benchmark — 35× fewer output tokens, identical UI](examples/efficiency-claim.png)

There is a second gain that is less obvious: **system prompt compilation**. The full A2UI vocabulary — 289 atoms, their fields, and descriptions — is compiled into a compressed reference via `scripts/gen_vocab.py` and injected once into the agent system prompt. Subsequent turns do not re-explain the design system. The model has what it needs from context; it just picks atoms and fills in values.

A Gemini agent primed with the vocabulary can produce a production-quality page schema in a single turn, consistently, every time. The vocabulary script and the benchmark are both in the repository.

> **At scale:** at Claude Sonnet 4 output token pricing, a 1,000-page workload generating raw HTML costs roughly **$4.9k/month** in output tokens alone. The same workload on A2UI costs under **$300**. The renderer is free.

---

## Meet Stage: the presentation surface

Google Meet Stage is an often-overlooked surface. It allows a participant to broadcast a web URL as a shared visual — effectively turning any web page into a slide that every participant sees simultaneously, with no PowerPoint required.

What makes it distinctive is the rendering context: **Chrome, full-screen, passive viewing**. The audience is not clicking. The page needs to communicate at distance, often on a projected display. This rules out small text, complex interactions, and anything requiring a CDN.

A2UI Meet Stage atoms are designed around these constraints:

- **Auto-playing animations** — `reveal_line` sweeps gradient text in from left using CSS clip-path; `word_reveal` fades words in one by one; `count_up_stat` rolls numbers from zero on page load. None of these require a user click.
- **Dark-first design** — `floating_orbs`, `dark_hero`, `glowing_stat`, `gradient_heading`, and `neon_text` are all designed for a dark background that reads well on a projected screen.
- **Large, high-contrast typography** — `clamp()`-based font sizing ensures headings scale from laptop to conference room display without manual adjustment.

Of the 289 atoms, **197 work on Meet Stage** — giving agents a rich palette for building live presentation pages.

Three use cases stand out on this surface:

**Dynamic meeting briefs.** A Gemini agent reads the meeting invite, attendee profiles, and linked documents via Workspace APIs. It generates an A2UI page — a full-screen brief with key context, talking points, and live document summaries rendered by Vertex AI — that the host shares on Meet Stage at the start of the call. The room is immediately oriented without anyone having to narrate a slide deck.

**Live D2 architecture diagrams.** D2 is a declarative diagramming language. A2UI can render D2 diagrams inline by embedding the diagram as a rendered SVG atom. An agent can generate a system architecture, data flow, or entity model diagram in D2 syntax, convert it to SVG, and embed it directly in a Meet Stage page — no Lucidchart export needed.

**Parallel participant experiences — the thing that makes Meet Stage genuinely different.** This is the use case that surprised me most. Meet Stage does not have to be passive. Because the shared visual is a URL, every participant can open it in their own browser tab — and now you have a live, multi-participant interactive experience running inside a Google Meet call, with no app to install, no QR code to scan.

Each participant navigates the content independently. Their responses, votes, or selections can pool into a shared data store in real time. The presenter sees live aggregation on their own view. It is closer to a Mentimeter or Slido session than a slide deck — except the entire experience is defined by an A2UI schema, generated by an agent from the meeting context, and requires zero additional infrastructure.

I built an early version of this for an aerospace GTM session: the deck was live on Meet Stage, participants voted on go-to-market priorities directly through the page, and the results updated in real time as people responded. [▶ Watch the aerospace GTM voting demo on YouTube]

The broader pattern — **agent-generated interactive briefs where every participant has a live, independent instance** — is one of the most interesting things Meet Stage makes possible. A2UI makes it practical by keeping the content generation in one JSON schema rather than a custom web app per session.

---

## Google Chat: structured cards as a first-class surface

Google Chat's Card v2 format is a structured card schema — a JSON document defining sections, widgets, buttons, chips, and images that render natively inside Chat messages. It is not HTML. It has its own vocabulary, its own layout engine, and its own constraints.

A2UI wraps Card v2 in the same catalogue model. An agent that wants to post a rich Chat message expresses its intent in A2UI schema; the Chat renderer converts it to native Card v2 JSON and sends it to the Chat API. The agent never touches Card v2 syntax directly.

The real power here is **pre-defined formats** — card structures that are fixed in shape but have AI-filled content:

**Arrivals** — When a new team member joins a Chat space, an agent triggers automatically: it pulls their Google profile, their public Drive files, their reported area of work, and generates a "Welcome to the team" card. Name, photo, role, what they are working on, three suggested people to connect with. The shape is always the same; the content is always relevant.

**Incident bridge** — A P1/P2 incident fires a structured card with severity badge, one-line description, assigned owner, war room link, and a timeline field that updates as the incident evolves. Every incident looks the same; on-call engineers know exactly where to look.

**Deployment digest** — A release pipeline posts a card: service name, version, changes (bullet list from git log), rollback command, deploy time. Consistent format, AI-summarised change notes.

**Sprint kickoff** — At the start of each sprint, an agent reads the sprint board and generates a card: sprint goal, team assignments, ceremony schedule, carry-over items. The PM never has to write the Monday message.

**Decision record** — When an architect marks a decision as final in a doc, an agent posts a card: decision title, rationale (AI-summarised from the doc), alternatives considered, approve/reject chips for stakeholders who still need to sign off.

**Daily digest** — A morning briefing card: three meetings on the calendar, three open tasks due today, one key metric from the team dashboard. Delivered at 08:30, generated in one Vertex AI call.

Chat currently has **26 atoms** in the catalogue. It is the surface with the most room to grow — and because the card format is fully defined, new atoms here are deterministic by nature.

---

## Apps Script Web App: the rendering engine model

The newest and most versatile surface is the **Apps Script web app**. This is where the rendering engine concept is most visible.

A single Apps Script deployment — one URL, one codebase — acts as a universal rendering engine. It receives a base64-encoded JSON payload as a URL parameter, decodes it, resolves each atom type, and returns a fully rendered HTML page. The page has no server, no database, no build pipeline, no hosting bill.

**The URL is the app. The JSON schema is the CMS.**

```
https://script.google.com/macros/s/{deployment-id}/exec?p={base64-encoded-schema}
```

To generate a new page, you change the schema. To share a page, you share the URL. To give someone access, you give them the URL. There are no deployments, no PRs, no infrastructure tickets.

The rendering engine diagram:

```d2
direction: right

intent: "Natural Language\nIntent" {shape: oval}
schema: "A2UI JSON\nSchema" {shape: document}
url: "base64 URL\nParameter" {shape: hexagon}
engine: "GAS Rendering\nEngine" {
  atoms: "Atom Library\n289 atoms" {shape: cylinder}
}
surface: "Live Web App" {shape: rectangle}

intent -> schema: Gemini generates
schema -> url: make_url.py encodes
url -> engine: HTTP GET
engine.atoms -> engine: resolves types
engine -> surface: renders HTML
```

The engine currently ships **9 renderer files** covering 278 atoms on the GAS web surface. Any atom type Gemini outputs that exists in the catalogue will render correctly. Atom types it invents will return a graceful "unknown atom type" fallback.

This model extends naturally to everything Google Workspace agents do:

- A Gemini agent that reads a spreadsheet and produces a dashboard — the dashboard is a GAS URL, live-rendered from the current data
- A meeting brief generated from a calendar event and linked docs — the brief is a GAS URL, shareable with all attendees before the call
- A weekly status report assembled from Tasks, Gmail, and Drive activity — the report is a GAS URL, consistent every week because the atoms define the layout

The surface is accessible in a way that raw HTML generation is not: **non-developers can describe what they want in plain English and receive a working, styled web app in seconds**.

---

## Broader canvas: a2py, GCP Guard, and the image parser idea

The catalogue model does not stop at Google Workspace UI surfaces.

**a2py** applies the same principle to Python environments — a vocabulary of rendering atoms for Jupyter notebooks, Streamlit apps, and FastAPI response bodies. A data scientist asks their AI assistant to summarise model performance; the assistant outputs an a2py schema; the renderer produces a structured, styled output cell rather than raw markdown. The design decisions are pre-compiled; the model focuses on the data.

**A2UI GCP Guard** is an early concept: a thin wrapper around the `gcloud` CLI that intercepts command output and passes it through an A2UI rendering pipeline. Instead of raw JSON from `gcloud compute instances list`, you receive a styled table with status pills, uptime indicators, and resource cost badges. Instead of a wall of log output from `gcloud logging read`, you receive a structured log viewer with severity badges and collapsible entries. The vocabulary is pre-compiled for GCP resource types; the display is always consistent.

**A deterministic image parser** is an idea I am still working through. The question is whether you can run the vocabulary model in reverse: feed an image — a screenshot, a mockup, a photo of a whiteboard layout — to Gemini Vision with the A2UI vocabulary in context, and ask it to express what it sees as a JSON atom schema. Not generate HTML from the image, but *classify* the visual into known atom types.

The interesting property of constraining the output to a known vocabulary is that it becomes deterministic in a way that open-ended image-to-HTML generation never is. Gemini might vary in how it describes a "two-column layout with a metric on the left" — but if it must choose between `split_stat`, `side_by_side_spec`, and `bento_grid`, it will tend to agree with itself across runs. The catalogue acts as a type system for visual structure.

Practically, this could be a second endpoint on the GAS rendering engine: submit an image URL, receive back the A2UI schema Gemini infers, edit it if needed, and render. A screenshot of a competitor page becomes a remixable A2UI template. A photo of a whiteboard layout becomes a shareable web page. A slide exported from Google Slides becomes a live, animated Meet Stage version.

Whether the inference is accurate enough to be useful at scale is an open question — but the architecture is straightforward, and the layered web app already has Vertex AI wired in.

---

## Adding atoms to the catalogue

The catalogue grows through contribution. Adding an atom requires three things:

1. **A schema entry** in `atoms/schema.yaml` — type name, description, fields, surface compatibility
2. **A renderer implementation** — a `_RENDERERS['atom_type']` function in the appropriate `.gs` file (or surface equivalent)
3. **A category entry** in `scripts/gen_vocab.py` — so the atom appears in the vocabulary injected into agent system prompts

When a new atom is added to the schema and the renderer, every agent primed with the vocabulary gains access to it on the next context refresh. The atom becomes part of the language the agent speaks.

If you have a UI pattern you keep building by hand — a particular card layout, a data display format, a notification structure — it is a candidate for the catalogue. Define it once. Let the agent use it forever.

---

## What this adds up to

A2UI is not a UI framework. It is a **shared language between humans and agents** for describing interfaces in Google Workspace.

The catalogue encodes the design decisions. The renderer makes them real. The agent speaks the vocabulary. The token spend drops by 5× per page. The outputs are consistent across every turn, every session, every surface.

As the catalogue grows, the language gets richer. As the renderer extends to new surfaces, the same vocabulary reaches further. As agents get better at reading the vocabulary, the quality of what they produce improves — not because the model changes, but because the vocabulary it reasons over becomes more precise.

That is the long game: a catalogue precise enough that describing *what* you want is the whole job, and *how it looks* is already decided.

**Substrates, not composites** — the atoms are the substrate. Agents, sessions, surfaces, and users are composites built on top of them. **Reuse, don't reinvent** — every atom added to the catalogue is a design decision that never needs to be made again.

---

---

## Further reading

**[A2UI: The Compiled Vocabulary Approach to Generative UI](https://techmusings.krygier.fr/post/a2ui-compiled-vocabulary)** — The theoretical underpinning of this whole project. How the catalogue-as-vocabulary model works, why compiled knowledge beats per-turn injection at scale, and the generative / runbook / hybrid agent paths that fall out of it. If the tokenomics section above felt interesting, this is the deeper cut.

**[Substrate, Not Slides: Building Google Meet Studio on A2UI 0.9](https://techmusings.krygier.fr/post/substrate-not-slides-a2ui-full)** — The Meet Stage surface explored at length: what makes it different from screen sharing, how the rendering pipeline works inside Google Meet's constraints, and why treating a URL as a slide deck is a more powerful idea than it first appears.

**[How I Got to A2UI](https://techmusings.krygier.fr/post/how-i-got-to-a2ui)** — The origin story. What problem I was actually trying to solve, the dead ends along the way, and why a vocabulary approach was the thing that finally clicked.

**[Wiring Gemini Enterprise Agent Platform to Google Workspace: Apps Script as the Bridge](https://techmusings.krygier.fr/post/agent-engine-workspace-bridge)** — The infrastructure side of the picture: how a GCP-hosted Gemini agent reaches into Workspace to read docs, calendar, Gmail, and Drive — and why Apps Script is currently the most practical bridge between the two.

---

*The A2UI Catalogue, renderer source, vocabulary scripts, and surface playbooks are a personal project maintained in the a2ui-catalogue repository. The GAS rendering engine is deployed as a stable Apps Script web app — one URL, 289 atoms, six surfaces. It is not affiliated with AG-UI, CopilotKit, or any third-party UI protocol.*
