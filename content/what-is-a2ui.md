---
title: "What is A2UI? The Agent-to-UI Protocol"
date: 2026-11-15
summary: "A2UI is an open protocol that lets AI agents show native UI from JSON. How it works, renderers, catalogs, macros, Express, and how it differs from HTML."
read_minutes: 13
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

## The SDKs

A2UI has three layers of SDK code. The **Core SDK** is the shared foundation: it reads and writes A2UI messages across protocol versions, applies them to a surface and its data model, and validates. The **Agent SDK** sits on your server and builds on it. From a catalog, its skill generator produces the prompt instructions and grammar rules. Its compiler parses what comes back, validates it against the catalog and emits the messages. The **Renderer SDK** sits in the client, builds on the same core and paints the messages with that platform's toolkit. The Agent SDK does not paint anything, and a renderer does not talk to the model.

Your own agent code sits outside the SDK. a2ui.org's overview puts it this way: your agent code and LLM runtime take the generated skill alongside your domain tools, call the model, and pass its UI output to the SDK's compiler. The model is optional. Your code can build the output itself, or send content authored in advance as a static payload.

<!-- SDK-DIAGRAM:START -->
### How the pieces fit together

The picture follows the stages on a2ui.org's overview page, as we read it on 15 November 2026. Read the arrows in the order of the steps table below the picture. The model is optional, because your own code can build the output, or send content authored in advance.

<div class="sdkfig" id="sdk-figure"><div class="sdkfig-motion"><div class="sdkfig-wide">@@SVG_SDK_WIDE_ANIM@@</div><div class="sdkfig-narrow">@@SVG_SDK_NARROW_ANIM@@</div><p class="sdkfig-controls"><button type="button" class="sdkfig-replay">Replay the animation</button> <span class="sdkfig-note">It plays once, in about four seconds, and then stays as the finished picture.</span></p></div><div class="sdkfig-still"><div class="sdkfig-wide">@@SVG_SDK_WIDE_STATIC@@</div><div class="sdkfig-narrow">@@SVG_SDK_NARROW_STATIC@@</div></div><details class="sdkfig-text"><summary>Text version of the diagram</summary><ol><li>The user types a request in the client app, or presses a button. The trigger goes to your agent code. (dashed arrow)</li><li>The renderer tells your agent which catalogs it can draw. It is sent along with the trigger. (dashed arrow)</li><li>In advance, the Agent SDK has generated a skill from the catalog: prompt instructions and grammar rules. Your agent loads it.</li><li>Your agent calls its domain tools, then prompts the model with the data and the skill. With no model, your code builds the output itself, or sends a static payload.</li><li>The model streams its answer in an inference format, Express or JSON, back to your agent. (dashed arrow)</li><li>Your agent passes the UI output to the Agent SDK&#x27;s compiler.</li><li>The compiler pulls the catalog and validates each component and its properties against it. Invalid output is reported, repaired or retried.</li><li>Where a macro is used, the compiler hands the call to the Macros, which expand it into a tree of components, and takes the tree back (Python only).</li><li>The compiler emits the A2UI messages: createSurface, updateComponents and updateDataModel, and deleteSurface when a surface is removed.</li><li>The messages are sent over a transport: AG-UI, A2A, MCP, WebSockets or your own.</li><li>At the app, the Core SDK applies the messages.</li><li>The Core SDK keeps the surface and its data model and passes them to the Renderer.</li><li>The Renderer draws the Native UI. The next trigger starts again at step 1.</li></ol><p>Not on the route: the protocol version, carried inside the messages (steps 9 to 11).</p></details><style>.sdkfig{margin:1.2rem 0}.sdkfig svg{display:block;width:100%;height:auto}.sdkfig-still{display:none}.sdkfig-controls{margin:.6rem 0 0;font-size:.92rem;color:var(--text-muted)}.sdkfig-replay{font:inherit;padding:6px 12px;border-radius:8px;border:1px solid var(--border-strong);background:var(--surface);color:var(--text);cursor:pointer}.sdkfig-replay:focus-visible{outline:2px solid var(--accent);outline-offset:2px}.sdkfig-text{margin-top:.6rem}.sdkfig-narrow{display:block}.sdkfig-wide{display:none}@media(min-width:1180px){.sdkfig-wide{display:block;width:1100px;position:relative;left:50%;transform:translateX(-50%)}.sdkfig-narrow{display:none}}@media(prefers-reduced-motion:reduce){.sdkfig-motion{display:none}.sdkfig-still{display:block}}</style><script>(function(){var box=document.getElementById("sdk-figure");if(!box)return;var svgs=box.querySelectorAll(".sdkfig-motion svg");function play(){for(var i=0;i<svgs.length;i++){var s=svgs[i];if(s.setCurrentTime){s.setCurrentTime(0);s.unpauseAnimations&&s.unpauseAnimations()}}}var b=box.querySelector(".sdkfig-replay");if(b)b.addEventListener("click",play);if("IntersectionObserver" in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){play();io.disconnect()}})},{threshold:.4});io.observe(box)}})();</script></div>

#### The route, step by step

| Step | Arrow | Label on the arrow | What happens |
|---|---|---|---|
| 1 | Native UI to Your agent code | trigger: request or action | The user types a request in the client app, or presses a button. The trigger goes to your agent code. |
| 2 | Renderer to Your agent code | capabilities | The renderer tells your agent which catalogs it can draw. It is sent along with the trigger. |
| 3 | Agent SDK to Your agent code | skill | In advance, the Agent SDK has generated a skill from the catalog: prompt instructions and grammar rules. Your agent loads it. |
| 4 | Your agent code to Model | prompt | Your agent calls its domain tools, then prompts the model with the data and the skill. With no model, your code builds the output itself, or sends a static payload. |
| 5 | Model to Your agent code | Express or JSON | The model streams its answer in an inference format, Express or JSON, back to your agent. |
| 6 | Your agent code to Agent SDK | UI output | Your agent passes the UI output to the Agent SDK's compiler. |
| 7 | Agent SDK to Catalog | pull and validate | The compiler pulls the catalog and validates each component and its properties against it. Invalid output is reported, repaired or retried. |
| 8 | Agent SDK to Macros | expand | Where a macro is used, the compiler hands the call to the Macros, which expand it into a tree of components, and takes the tree back (Python only). |
| 9 | Agent SDK to A2UI messages | messages | The compiler emits the A2UI messages: createSurface, updateComponents and updateDataModel, and deleteSurface when a surface is removed. |
| 10 | A2UI messages to Transport | sent over | The messages are sent over a transport: AG-UI, A2A, MCP, WebSockets or your own. |
| 11 | Transport to Core SDK | apply | At the app, the Core SDK applies the messages. |
| 12 | Core SDK to Renderer | surface, data model | The Core SDK keeps the surface and its data model and passes them to the Renderer. |
| 13 | Renderer to Native UI | draws | The Renderer draws the Native UI. The next trigger starts again at step 1. |

#### The key concepts

The protocol version is the one concept with no step of its own: every message carries it.

| Concept | What it is | Lives in | On the route |
|---|---|---|---|
| Trigger | What starts a turn: the user's request typed in the client app, or an action, an event with a name and context that a component sends back when the user presses it. It goes to your agent. | client to agent | 1 |
| Capability negotiation | The renderer lists the catalogs it can draw, sent along with its messages (with every message in v0.9.1; scoped to a turn or a session in v1.0). The agent picks a match when it creates a surface. An agent can also advertise the catalogs it can generate, for example in an A2A Agent Card. | both sides | 2 |
| Skill | The prompt instructions and grammar rules the SDK's skill generator produces from the catalog, in advance. Your agent loads it to prompt the model. (a2ui.org: "the SDK's skill generator produces an A2UI skill".) | your server | 3 |
| Your agent code | Your code and LLM runtime, outside the SDK. It takes the trigger, calls its domain tools (for example a flight search), loads the skill, prompts the model and passes the UI output to the SDK. With no model it can build the output itself, or send content authored in advance as a static payload. | your server | 1 to 6 (receives 1, 2, 3, 5; sends 4, 6) |
| Model (optional) | Writes the screen in an inference format when one is used. A scripted agent, or a static payload, needs no model. | agent side | 4, 5 |
| Inference format | How the model writes a screen: Direct JSON, Express (compact, the Python processor default) and the experimental Atom and Elemental formats (Python only). The same catalogs and examples work with each. The SDK's "Atom" format is not one of our catalogue atoms. See [What is A2UI Express?](#what-is-a2ui-express). | agent side | 5 |
| Agent SDK | A library, not the agent. Its skill generator makes the skill from the catalog; its compiler parses the UI output as it streams in, validates it against the catalog (repairing and retrying invalid output) and emits the wire messages. It builds on the Core SDK and imports no agent framework; integrations such as a2ui-a2a and a2ui-adk are separate packages. | your server | 3, 6, 7, 8, 9 |
| Catalog | The set of components and functions an agent may use: the Basic Catalog, or a custom one, described as JSON Schema (a catalog.json). Named by a catalogId. The SDK pulls from it to generate the skill and to validate the output. See [Basic Catalog](/what-is-a2ui/basic-catalog/) and [Custom catalog: how to](/what-is-a2ui/custom-catalog/how-to/). | both sides | 7 (and 3, in advance) |
| Macro | A Python function that appears to the model as a component in its catalog and expands into standard components on the server before the message is sent. A resolver can inject data on the server. Python only today. See [Macros](#macros-the-model-writes-one-call-the-server-writes-the-tree). | agent side | 8 |
| A2UI messages | createSurface, updateComponents, updateDataModel and deleteSurface. Each is a JSON object with a version and exactly one message-type key. | the wire | 9 (carried through 10 and 11) |
| Protocol version | Which set of message rules both sides follow: v0.8, v0.9, v0.9.1 or v1.0. It is in every message and, for A2A, in the extension URI. Catalogs name the version they target. It is not the package version: a2ui-agent-sdk 0.11.0 does not speak protocol 0.11. | both sides | No step of its own: carried inside every message (steps 9 to 11) |
| Transport | How the messages travel. A2UI is transport-agnostic: any channel that carries JSON in order, with framing and metadata, and a return path for actions. a2ui.org names AG-UI, A2A, MCP and WebSockets. ADK is an agent framework: its package converts to A2A parts. An agent and a renderer can even share one process, so no network is needed. | the wire | 10, 11 |
| Core SDK | The shared foundation under both sides: reads and writes messages across protocol versions, applies them to surface, component and data models, resolves pointers and validates. The Agent SDK and the renderer both build on it, one per language. | both sides | 11, 12 |
| Surface | One UI an agent builds: a component tree plus a data model, tied to a catalog when it is created. Many surfaces can exist at once. | client side | 12 |
| Data model | The values components bind to by path (JSON Pointer). updateDataModel changes them without resending the tree; a local edit updates the bound controls and sends nothing to the agent. | client side | 12 |
| Renderer | Paints a surface with the platform's toolkit and binds reactive values: React, Lit, Angular, Flutter, SwiftUI, Jetpack Compose. | client side | 2, 12, 13 |
<!-- SDK-DIAGRAM:END -->

### Package versions, installs and painting

Package version numbers are not protocol versions. `a2ui-agent-sdk` 0.11.0 does not speak protocol 0.11, and `@a2ui/react` 0.15.0 does not speak protocol 0.15. A common start is two installs, `pip install a2ui-agent-sdk` for the agent and a web renderer such as `npm install @a2ui/react`. It is not the only pairing: a TypeScript or Dart app can use the agent and the renderer in one language.

A renderer does not necessarily paint everything you send. On 15 November 2026 we ran each of three web renderers once. We took the published atoms that have a Basic example, 551 in all, and reduced each to Basic components. 538 painted on all three. By renderer, 539 painted on `@a2ui/react` 0.15.0, 541 on `@a2ui/lit` 0.15.0 and 540 on `@a2ui/angular` 0.14.0. The other 22 published atoms have no Basic example and were left out. "Painted" here means the example did not crash and drew some text, image, input or element. It is not a check that the result is correct, and it says nothing about what an arbitrary message will do, so test your own messages on each renderer you target.

### What the model writes
`a2ui-agent-sdk` 0.11.0 ships four formats. Direct JSON is the full A2UI messages. Express is a compact format that the SDK compiles into messages, and it is the processor's default, so the upstream documentation starts from Express. The package description says Direct JSON and Express both stream. The other two are marked experimental in the code: the Atom format, which uses parenthesised expressions, and Elemental, which looks like HTML. We have used the package, and we have not run the Atom or Elemental formats. The known-gaps file of the TypeScript `@a2ui/agent` package says "Express does not stream", and we have not run that. The Atom format is an experimental notation. It is not a component in our catalogue.

### After the model writes
A macro expands one short call into a full tree of components on the server, so the renderer never sees the macro. Macros are in the Python SDK only. The A2UI project's macros guide says macros are in the Python agent SDK, with other languages coming next.

### Published packages, as of 15 November 2026
| | Python | TypeScript | Dart |
|---|---|---|---|
| Agent package | a2ui-agent-sdk 0.11.0 (core: a2ui-core 0.6.0) | @a2ui/agent 0.1.0 (core: @a2ui/web_core 0.15.0) | a2ui_agent 0.3.0 (core: a2ui_core 0.7.0) |
| Direct JSON | yes | yes | yes |
| Express | yes | yes | yes |
| Atom format, Elemental | experimental | no | no |
| Macros | yes | no | no |
| Catalog load, system prompt, output validation | yes | yes | yes |
| A2A, ADK | no in this package; separate packages a2ui-a2a 0.3.0 and a2ui-adk 0.3.0 (`pip install "a2ui-adk[a2a]"` adds the A2A converters; plain `a2ui-adk` is the tools) | no | no |
| Protocol versions named by the upstream docs | v0.8, v0.9.1, v1.0 | v0.9.1, v1.0 | v0.9.1, v1.0 |
| Renderers | none | @a2ui/react 0.15.0, @a2ui/lit 0.15.0, @a2ui/angular 0.14.0 | a2ui_flutter 0.3.0 (Flutter) |

The SDK page says every v0.9.1 package accepts v0.9 wire envelopes and catalog IDs. The Python extension package versions come from PyPI's index and the files `a2ui_a2a-0.3.0-py3-none-any.whl` and `a2ui_adk-0.3.0-py3-none-any.whl`, both listed by PyPI's index as uploaded on 10 November 2026. The a2ui-a2a project page we saw still showed 0.1.0 only, so if your install resolves 0.1.0, pin `a2ui-a2a==0.3.0`. The TypeScript and Dart "no" cells come from file lists and searches of the packages, not a full read. TypeScript's known-gaps file says the Elemental and Atom formats "remain unimplemented". "Experimental" is upstream's own word in the code.

The upstream docs list React, Lit and Angular as v0.8, v0.9.1 and v1.0. None of the published packages exports `./v1_0`. React and Angular export `./v0_8` and `./v0_9`, and Lit also exports `./0.8` and `./ui`. React 0.13.0 moved the package root to a version-agnostic runtime. The "(v1_0)" lines are under "## 0.14.0" in the React 0.15.0 and Lit 0.15.0 changelogs, and under "## 0.13.0" in the Angular 0.14.0 changelog. Check which import your version expects.

### Not on a package registry
- Swift: SwiftUI renderer and a core, installed with Swift Package Manager from the A2UI repository (we saw the tag `v0.10.0+swift`, and have not tested whether Swift Package Manager resolves it). It has no agent SDK. The repo has a client-side `PayloadValidator` for messages it receives. We found no model-output check, and we did not run it.
- Android: two separate things. The renderer is Google's AndroidX Compose library. Its package number is 1.0.0-alpha02, which is a Maven version, not a protocol version. Upstream's SDK page lists the Compose renderer as protocol v0.9.1. We have not looked inside it. The agent side is `kotlin/agent_sdk_legacy` in the A2UI repository: Kotlin, still being edited, unpublished. Its tree has `A2aHandler.kt` and `SendA2uiToClientToolset.kt`, which we did not run. Its docs name v0.8 and v0.9, and we did not verify v1.0.
- Go, Rust, C# and Java: no official SDK on upstream's SDK page. That page points to community Go libraries, which we have not checked.

### Our reading
Python is the furthest ahead on the agent side. TypeScript and Dart have Direct JSON and Express. Swift and Kotlin are mostly renderer or legacy. We have not measured whether server-side macros make output more predictable.

### SDKs can lag the spec
In v1.0 a component from a different catalog than the surface's default carries the key `@catalogId`. The `createSurface` message still uses `catalogId`. The component-level key used to be spelled `catalogId`. Upstream changed it on 11 November 2026 (pull request #4044), after Python SDK 0.11.0 was released on 10 November 2026.

On 15 November 2026 we validated one surface with the Python SDK's validator, once with each spelling on a component from a second catalog. With `a2ui-agent-sdk` 0.11.0 and `a2ui-core` 0.6.0, `catalogId` passed and `@catalogId` failed with "Unrecognized component type 'Badge'" and "Unrecognized reserved protocol directive '@catalogId'". The message processor in `a2ui-core` 0.6.0 raised no error, but it put the component in the Basic catalog and kept `@catalogId` as an ordinary property. On a checkout of upstream's main branch (commit 6ac77a0610, 11 November 2026) both spellings passed. None of the published packages we checked contains the change.

The `a2ui_flutter` 0.3.0 README still tells the agent to name a custom component's catalog in `catalogId`, and we have not checked which spelling that package accepts. The macros guide on a2ui.org also still prints `catalogId` in its examples. Pin the SDK version you test with, and check its date. The [custom catalog how-to](/what-is-a2ui/custom-catalog/how-to/) shows the case in detail.

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
A compact format Google proposed on 27 October 2026 for a model to write a screen, instead of the full A2UI JSON. It is now in the published SDKs: `a2ui-agent-sdk` 0.11.0 for Python, `@a2ui/agent` 0.1.0 for TypeScript and `a2ui_agent` 0.3.0 for Dart. In our small test on this catalog it used fewer output tokens on every model we tried, and Google's 80 times claim was not confirmed.

### What does an A2UI SDK do?
It sits between a model and a renderer. On the agent side it builds the system prompt from a catalog, reads what the model writes, checks it against the catalog and turns it into A2UI messages. On the renderer side it processes those messages. The Python SDK also expands macros.

### Does the Python SDK accept @catalogId?
Not in the latest published release. The v1.0 spec writes a component's own catalog as `@catalogId`. With `a2ui-agent-sdk` 0.11.0 (10 November 2026) the validator rejects it, and the message processor in `a2ui-core` 0.6.0 raises no error but puts the component in the Basic catalog and keeps `@catalogId` as an ordinary property. Upstream's main branch reads both spellings since 11 November 2026, and no release has it yet. The paragraph under "SDKs can lag the spec" has the details.

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
