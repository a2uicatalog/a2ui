---
title: "What is A2UI? The Agent-to-UI Protocol"
date: 2026-11-15
summary: "A2UI is an open protocol that lets AI agents show native UI from JSON. How it works, renderers, catalogs, macros, Express, and how it differs from HTML."
read_minutes: 12
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
and MCP, and it also runs over server-sent events, WebSockets or plain REST. Version 1.0
is the current specification and 0.9.1 the previous one. Renderers say which
version and which catalogs they support, so an agent can send what each one understands:
the catalog's emitter, for example, sends v0.9 to Google's Android renderer and v1.0 elsewhere.

<!-- FILM -->

Google maintains official renderers for React, Lit, Angular, Flutter (the GenUI SDK) and
Jetpack Compose, with SwiftUI planned; a2ui.org also
[lists community renderers](https://a2ui.org/reference/renderers/).

## What is an A2UI renderer?

A renderer is the part of an app that turns A2UI messages into interface. It holds the catalogs it supports, reads each message the agent sends and draws the components with the app's own code, escaping text and checking links on the way. When the user presses a button or submits a form, the renderer sends that action back to the agent.

The agent never sends code, so the renderer decides what can appear on screen, and each app draws a component in its own style. A renderer also says which protocol version and which catalogs it supports, so an agent can send what it understands.

The official and community renderers are listed above. To see one at work, the [Basic Catalog Demos](/what-is-a2ui/basic-catalog/demos/) run the official React renderer in your browser.

## What is a catalog? The Basic Catalog and custom catalogs

A catalog is the list of components an agent may use, with the fields each one takes. It is the contract between the agent and the renderer: the agent can ask only for what the catalog names.

A2UI ships a **Basic Catalog** of @@BASIC_N@@ components and @@BASIC_FN@@ functions in version 1.0, covering text, layout, images, buttons and inputs. A renderer that supports it can draw any surface built from it, with no custom code. [See what it can do](/what-is-a2ui/basic-catalog/).

A **custom catalog** adds components of your own, such as a chart, a timeline or a comparison table. The app registers it with its renderer first, so an agent can use a custom component only where the host has done that. The [A2UI Atomic Catalog](/) below is a custom catalog. To build your own, read [How to make an A2UI custom catalog](/what-is-a2ui/custom-catalog/how-to/).

## Macros: the model writes one call, the server writes the tree

We <span role="img" aria-label="love">❤️</span> macros at a2uicatalog.ai

A macro is a function on the application server. The model writes one short call, and the
server expands it into ordinary A2UI components before anything reaches the renderer, so the
renderer never sees a macro. The upstream
[Using Macros](https://a2ui.org/guides/macros/) guide, in its "How macros work" section,
lists four reasons to use them:

- "Reduce output tokens and latency by letting the model write one call instead of a nested component tree."
- "Keep layouts consistent across turns because your server code constructs the component hierarchy."
- "Look up data from server-side databases and APIs, accepting an identifier from the model and populating the components on the server."
- "Ship new domain components with a server deployment alone, using catalog components the client already renders."

One measured example from this catalog's own tests (not yet published): asked to draw the latest run of five
workflows of a public repository, the model wrote this (the first two stages are shown, the
rest is elided):

```
root = IsoPipeline("Latest run of five a2uicatalog/a2ui workflows",
  [{name: "c567e65", kind: "commit", state: "latest"},
   {name: "build-apps", kind: "build", state: "passed"}, ...three more stages...], "teal")
```

The model's whole reply, the call inside its `<a2ui>` tags, was 365 bytes (173 output tokens),
identical in all ten runs on Claude Sonnet 5.5. The server expanded it into 37,728 bytes of
A2UI: five stock Basic Catalog components (a Card, a Column, a title Text, an Image and a
caption Text), with the picture carried in the Image. The saving is in output, not input: the
system prompt that carries the macro was about 5,100 input tokens, against about 1,300 for a
prompt that had the model draw the picture itself. This was one scene, one prompt and one
machine.

Limits: per the guide, "Macros are currently available in the Python agent SDK
(`a2ui-agent-sdk`), with support for other languages coming next." By default, a macro that
raises an argument or runtime exception during expansion is logged and left unexpanded so its
sibling components still expand, and client renderers do not implement unexpanded macro
components; the server can instead be set to raise so an agent can retry. Structural errors,
such as recursion, catalog errors and protocol-version mismatches, always raise. In the Image
approach, each patch reloads the whole image, and reduced-motion preferences are not honoured
inside an Image's SVG (tested in Chromium).

The A2UI project's own guide to macros is [Using Macros on a2ui.org](https://a2ui.org/guides/macros/). When we package our own macros to share them, we call the bundle a macro pack. The Demo Gallery has live examples: [Macro Packs](/what-is-a2ui/macro-packs/).

## What is A2UI Express?

Express is a compact format for a model to write a screen: instead of the full A2UI JSON, the model writes a short line, and the SDK expands it into A2UI messages. Google published it on 27 October 2026. The same SDK has two other formats: Direct JSON, the existing one, and Elemental, which looks like HTML.

We tested Express on this catalog as it stood in late October 2026, with six briefs and seven models. Express used fewer output tokens on every model we tried. Google's claim of 80 times was not confirmed in our tests. It is a small sample, and the [full results](/blog/020-a2ui-express-testing-results/) show the models, the counts and the limits.

## How far can the Basic Catalog go?

The Basic Catalog has few components; three techniques build more on top of them. Macros let
a server build larger trees from a short call. An Image can carry an animated picture that
small patches update. A Connect Four game has also been built on the stock components (Text,
Image, Row, Column and Button), with the board drawn as one picture by server code and
ordinary buttons for the moves; it is not yet published. Each has limits; the macro example
above is the only one measured on this page.

## The A2UI Atomic Catalog

A2UI defines a small Basic Catalog: text, rows, columns, cards, buttons, images and a few
inputs. Real answers need more: stat cards, charts, timelines, comparison tables, status
boards, animated explainers.

The [A2UI Atomic Catalog](/) is an open-source (MIT) catalog of @@ATOMS@@ published components,
each with typed fields, a JSON Schema and a live preview. Browse them in the
[A2UICatalog Explorer](/atoms/). Agents reach it through an MCP
server at `a2uicatalog.ai/mcp`, or read its machine-readable vocabulary at
[`/spec.json`](/spec.json). How it is built as an A2UI custom catalog, with the real files:
[A2UI custom catalog: a worked example](/what-is-a2ui/custom-catalog/). To make your own, see
[How to make an A2UI custom catalog](/what-is-a2ui/custom-catalog/how-to/), and for what A2UI ships with, the
[A2UI Basic Catalog](/what-is-a2ui/basic-catalog/).

## Where it runs

| Surface | How |
|---|---|
| Web | the catalog's web renderer |
| Google Workspace | Apps Script web apps and side panels, Google Chat cards, Meet stages |
| MCP Apps hosts | Claude, ChatGPT, [Gemini Enterprise](/blog/011-gemini-enterprise-mcp-apps-setup/) and other hosts that display MCP Apps views |
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

## A2UI and AG-UI

The names give it away. A2UI is about the user **interface**: which components to show and
what data they hold. AG-UI, the [Agent–User Interaction protocol](https://docs.ag-ui.com/introduction),
is about the **interaction**: the live connection between an agent backend and an app, carrying
messages, tool calls, state updates and the user's actions as a stream of events.

They stack rather than compete. An A2UI surface can travel inside an AG-UI stream; CopilotKit,
for example, sends it as an `ActivitySnapshot` event. As a2ui.org puts it, "use AG-UI as the
pipe, A2UI as the content." The film above shows the same thing: AG-UI is one of the pipes,
and the A2UI letter rides inside it.

## Get started

1. **Browse** the [catalog](/) and open any atom to see its fields and a live preview.
2. **Try it** in an MCP host: add the a2uicatalog MCP server, ask for a dashboard, and the
   host renders it.
3. **Render it yourself** on the web, in Apps Script, or on Android with
   `implementation("ai.a2uicatalog:atomic-catalog:0.1.0")`.
4. **Run the Basic Catalog demos** in your browser: the [Demo Gallery](/what-is-a2ui/basic-catalog/demos/) shows each component and a trip planner built only from them.

## FAQ

### Is A2UI a Google project?
Google created it, with contributions from CopilotKit and the open-source community, and it
is developed in the open at [github.com/a2ui-project/a2ui](https://github.com/a2ui-project/a2ui).
The A2UI Atomic Catalog is an independent open-source catalog built on it.

### Does the agent generate HTML?
No. It sends JSON that names components. The renderer draws them with code the app trusts.

### What happens if an agent asks for a component the app doesn't have?
That depends on the renderer. Google's Android renderer refuses unknown types, so the
catalog's emitter reads which catalogs an app supports and sends a simpler version to apps
that lack them.

### Which AI models can use it?
Any model that can produce JSON. The catalog's MCP server and per-atom JSON Schemas help
models produce valid payloads.

### Is it free?
Yes. The protocol is Apache 2.0, and the A2UI Atomic Catalog is MIT-licensed.

### How is A2UI different from AG-UI?
A2UI describes the user interface. AG-UI, the Agent–User Interaction protocol, carries the
interaction between an agent and an app: messages, tool calls, state and user actions. A2UI
often travels over AG-UI; as a2ui.org puts it, "use AG-UI as the pipe, A2UI as the content."

### What is an A2UI renderer?
The part of an app that turns A2UI messages into interface. It draws the components with the app's own code, escapes text, checks links and sends the user's actions back to the agent. Google's official renderers cover React, Lit, Angular, Flutter and Jetpack Compose.

### What is the difference between the Basic Catalog and a custom catalog?
The Basic Catalog is the set of components and functions A2UI ships with, and a renderer that supports it needs no custom code. A custom catalog adds components of your own, such as charts, and the app registers it with its renderer before an agent can use them.

### What is A2UI Express?
A compact format Google proposed on 27 October 2026 for a model to write a screen, instead of the full A2UI JSON. In our small test on this catalog it used fewer output tokens on every model we tried, and Google's 80 times claim was not confirmed.

### Where does macro expansion happen?
On the application server, before the messages reach the renderer. The renderer receives
ordinary components and never sees the macro.

### Which languages support macros?
The upstream guide says macros are currently available in the Python agent SDK, with support
for other languages coming next.

### What happens if a macro fails?
By default, a macro that raises an argument or runtime exception during expansion is logged
and left unexpanded, so sibling components still expand. Client renderers do not implement
unexpanded macro components. The server can instead be set to raise, so an agent can send the
error back to the model. Structural errors, such as recursion, catalog errors and
protocol-version mismatches, always raise.
