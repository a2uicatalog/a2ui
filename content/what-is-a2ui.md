---
title: "What is A2UI? The Agent-to-UI Protocol"
date: 2026-10-05
summary: "A2UI is a declarative protocol that lets AI agents generate native UI from JSON. Learn how it works, where to use it, and how it differs from generated HTML."
read_minutes: 5
---


# What is A2UI? The Agent-to-UI Protocol

In the words of [a2ui.org](https://a2ui.org/introduction/what-is-a2ui/), "A2UI (Agent to UI)
is a declarative UI protocol for agent-driven interfaces." In practice it lets an AI agent
show a user real interface instead of writing HTML. The agent sends a stream of JSON that
names components, such as a chart, a form or a checklist, and fills in their data. The app
draws those components with its own trusted code. The agent never sends code, so what can
appear on screen is whatever the app has chosen to support.

A2UI was created by Google, with contributions from CopilotKit and the open-source
community, and is developed in the open at
[github.com/a2ui-project/a2ui](https://github.com/a2ui-project/a2ui) under the Apache 2.0
licence.

## Why not just generate HTML?

Most agents answer in text, or ask a model to write HTML. Text can't show a chart. Generated
HTML is slow, inconsistent and hard to make safe, because the app is now running markup a
model wrote.

A2UI splits the job. The model picks components from a catalog and supplies their data;
the renderer turns them into native UI. A catalog is the contract between the two: the
agent can only ask for components the renderer has registered.

That contract is also the security model. A component's fields are data, such as a label,
a number or a URL, and the renderer decides how to draw them, escaping text and checking
links as it would for any other input. A model can't slip script or markup onto the page,
because the payload has nowhere to carry it.

## How it works

The agent streams four kinds of message to the renderer:

- `createSurface` opens a new surface (a panel, a card, a page).
- `updateComponents` adds or changes components on it.
- `updateDataModel` changes the data those components are bound to.
- `deleteSurface` removes it.

Because data is separate from structure, the renderer can draw progressively as messages
arrive, and an agent can update one number without resending the whole screen. When a user
acts (presses a button, submits a form) the renderer sends the action back to the agent.

The protocol doesn't care how messages travel. The spec describes bindings for AG-UI, A2A
and MCP, and it also runs over server-sent events, WebSockets or plain REST. Version 0.9.1
is the current production release and 1.0 is a release candidate. Renderers say which
version and which catalogs they support, so an agent can send what each one understands:
the catalog's emitter, for example, sends v0.9 to Google's Android renderer and v1.0 elsewhere.

<!-- FILM -->

Google maintains official renderers for React, Lit, Angular, Flutter (the GenUI SDK) and
Jetpack Compose, with SwiftUI planned; a2ui.org also
[lists community renderers](https://a2ui.org/reference/renderers/).

## The A2UI Atomic Catalog

A2UI defines a small Basic Catalog: text, rows, columns, cards, buttons, images and a few
inputs. Real answers need more: stat cards, charts, timelines, comparison tables, status
boards, animated explainers.

The [A2UI Atomic Catalog](/) is an open-source (MIT) catalog of 545 published components,
each with typed fields, a JSON Schema and a live preview. Agents reach it through an MCP
server at `a2uicatalog.ai/mcp`, or read its machine-readable vocabulary at
[`/spec.json`](/spec.json).

## Where it runs

| Surface | How |
|---|---|
| Web | the catalog's web renderer |
| Google Workspace | Apps Script web apps and side panels, Google Chat cards, Meet stages |
| MCP Apps hosts | Claude, ChatGPT and other hosts that display MCP Apps views |
| Android | Google's `androidx.a2ui` Jetpack Compose renderer plus the [atomic-catalog library](/surfaces/android/) |
| Claude Code | a plugin that draws atoms in terminal panes |
| Email and PDF | static renders for the atoms that suit them |

Each [surface page](/surfaces/android/) lists exactly which components work there.

## A2UI and MCP

They do different jobs and work together. MCP connects a model to tools and data. A2UI
describes interface. An MCP tool can return an A2UI surface, so an agent that uses MCP can
also show UI.

MCP Apps is the closer comparison. As a2ui.org puts it, MCP Apps "treat UI as a resource":
a server provides pre-built HTML that the host shows in a sandboxed frame. A2UI instead
sends component blueprints and leaves styling and rendering to the host. The two combine
well: the catalog's renderer runs inside an MCP Apps view, so one A2UI payload reaches
every MCP Apps host. There's more on this in
[MCP Apps isn't A2UI's competitor](/blog/007-mcp-apps-portability/).

## Get started

1. **Browse** the [catalog](/) and open any atom to see its fields and a live preview.
2. **Try it** in an MCP host: add the a2uicatalog MCP server, ask for a dashboard, and the
   host renders it.
3. **Render it yourself** on the web, in Apps Script, or on Android with
   `implementation("ai.a2uicatalog:atomic-catalog:0.1.0")`.

## FAQ

**Is A2UI a Google project?**
Google created it, with contributions from CopilotKit and the open-source community, and it
is developed in the open at [github.com/a2ui-project/a2ui](https://github.com/a2ui-project/a2ui).
The A2UI Atomic Catalog is an independent open-source catalog built on it.

**Does the agent generate HTML?**
No. It sends JSON that names components. The renderer draws them with code the app trusts.

**What happens if an agent asks for a component the app doesn't have?**
That depends on the renderer. Google's Android renderer refuses unknown types, so the
catalog's emitter reads which catalogs an app supports and sends a simpler version to apps
that lack them.

**Which AI models can use it?**
Any model that can produce JSON. The catalog's MCP server and per-atom JSON Schemas help
models produce valid payloads.

**Is it free?**
Yes. The protocol is Apache 2.0, and the A2UI Atomic Catalog is MIT-licensed.

**How is A2UI different from AG-UI?**
AG-UI is a transport: it connects an agent backend to a frontend with real-time state sync.
A2UI is the UI format that travels over it. a2ui.org's summary is the clearest: "use AG-UI
as the pipe, A2UI as the content."
