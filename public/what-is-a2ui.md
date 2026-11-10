---
title: What is A2UI? The Agent-to-UI Protocol
description: A2UI is a declarative protocol that lets AI agents generate native UI from JSON. Learn how it works, where to use it, and how it differs from generated HTML.
canonical: https://a2uicatalog.ai/what-is-a2ui/
generated_by: gen_page_twins.py
---

# What is A2UI? The Agent-to-UI Protocol

A2UI was created by Google, with contributions from CopilotKit and the open-source community, and is developed in the open at [github.com/a2ui-project/a2ui](https://github.com/a2ui-project/a2ui) under the Apache 2.0 licence.

## Why not just generate HTML?

Most agents answer in text, or ask a model to write HTML. Text can't show a chart. Generated HTML is slow, inconsistent and hard to make safe, because the app is now running markup a model wrote.

A2UI splits the job. The model picks components from a catalog and supplies their data; the renderer turns them into native UI. A catalog is the contract between the two: the agent can only ask for components the renderer has registered.

That contract is also the security model. A component's fields are data, such as a label, a number or a URL, and the renderer decides how to draw them, escaping text and checking links as it would for any other input. A model can't slip script or markup onto the page, because the payload has nowhere to carry it.

## How it works

The agent streams four kinds of message to the renderer:

- `createSurface` opens a new surface (a panel, a card, a page).
- `updateComponents` adds or changes components on it.
- `updateDataModel` changes the data those components are bound to.
- `deleteSurface` removes it.

Because data is separate from structure, the renderer can draw progressively as messages arrive, and an agent can update one number without resending the whole screen. When a user acts (presses a button, submits a form) the renderer sends the action back to the agent.

The protocol doesn't care how messages travel. The spec describes bindings for AG-UI, A2A and MCP, and it also runs over server-sent events, WebSockets or plain REST. Version 0.9.1 is the current production release and 1.0 is a release candidate. Renderers say which version and which catalogs they support, so an agent can send what each one understands: the catalog's emitter, for example, sends v0.9 to Google's Android renderer and v1.0 elsewhere.

1 · THE LETTER1 · THE LETTER

A2UI is the letter.A2UIis the letter.

Declarative JSON: it names components from a catalog, with their data.Declarative JSON: it namescomponents from a catalog,with their data.

letter.a2ui.json

{ "version": "v1.0", "createSurface": { "surfaceId": "jobs", "catalogId": "…/a2ui-atoms-v1.json", "components": [ { "id": "a", "component": "stat_card", "label": "Open jobs", "value": "12" }, { "id": "b", "component": "motion_chart", "kind": "bars", "data": [4, 7, 5, 9] }, { "id": "c", "component": "motion_checklist", "items": ["Quote", "Book", "Pay"] }, { "id": "root", "component": "Column", "children": ["a", "b", "c"] } ] } }

{ "version": "v1.0",

 "createSurface": { "surfaceId": "jobs",

 "catalogId": "…/a2ui-atoms-v1.json",

 "components": [

 { "id": "a", "component": "stat_card",

 "label": "Open jobs", "value": "12" },

 { "id": "b", "component": "motion_chart",

 "kind": "bars", "data": [4, 7, 5, 9] },

 { "id": "c", "component": "motion_checklist",

 "items": ["Quote", "Book", "Pay"] },

 { "id": "root", "component": "Column",

 "children": ["a", "b", "c"] } ] } }

A2UI is the letter: it names components and never carries code.A2UI is the letter: it names components

and never carries code.

2 · THE ENVELOPE2 · THE ENVELOPE

Each pipe has its own envelope.Each pipe has its own envelope.

A2UIA2UI

tool result

A2UIA2UI

activity snapshot

A2UIA2UI

data part

MCPMCP

AG-UIAG-UI

A2AA2A

The letter inside never changes.The letter inside never changes.

3 · THE PIPE3 · THE PIPE

Then it travels.Then it travels.

AG-UI · e.g. CopilotKitAG-UI · e.g. CopilotKit

MCP · Claude, ChatGPTMCP · Claude, ChatGPT

A2A · agent to agentA2A · agent to agent

agentagent

hosthost

Any pipe will carry it.Any pipe will carry it.

4 · THE LAST HOP4 · THE LAST HOP

The surface is the last hop.The surface is the last hop.

Claude · ChatGPT

Chat

Open jobs

12

4

7

5

9

Quote

Book

Pay

CopilotKit

Chat

Open jobs

12

4

7

5

9

Quote

Book

Pay

Google Workspace

Chat

Open jobs

12

4

7

5

9

Quote

Book

Pay

Open jobs

12

4

7

5

9

Quote

Book

Pay

MCP Apps sandboxed viewMCP Appssandboxed view

Web app React rendererWeb appReact renderer

Google Workspace Apps Script web appGoogle WorkspaceApps Script web app

Android androidx.a2uiAndroidandroidx.a2ui

Each surface's renderer draws the letter in its own style.Each surface's renderer draws the letter in its own style.

WHERE THE COMPONENTS COME FROMWHERE THE COMPONENTS COME FROM

a2uicatalog.aia2uicatalog.ai

The components a letter can name, and the renderers that draw them on each surface.The components a letter can name, and the renderersthat draw them on each surface.

500+ components◆500+ components

Web · MCP Apps · Google Workspace · Android▣Web · MCP Apps · Google Workspace · Android

Write the letter once. Every surface can draw it.Write the letter once. Every surface can draw it.

0:00

How agent UI protocols nest

Google maintains official renderers for React, Lit, Angular, Flutter (the GenUI SDK) and Jetpack Compose, with SwiftUI planned; a2ui.org also [lists community renderers](https://a2ui.org/reference/renderers/).

## The A2UI Atomic Catalog

A2UI defines a small Basic Catalog: text, rows, columns, cards, buttons, images and a few inputs. Real answers need more: stat cards, charts, timelines, comparison tables, status boards, animated explainers.

The [A2UI Atomic Catalog](https://a2uicatalog.ai/) is an open-source (MIT) catalog of 545 published components, each with typed fields, a JSON Schema and a live preview. Agents reach it through an MCP server at `a2uicatalog.ai/mcp`, or read its machine-readable vocabulary at [`/spec.json`](https://a2uicatalog.ai/spec.json).

## Where it runs

| Surface | How |
|---|---|
| Web | the catalog's web renderer |
| Google Workspace | Apps Script web apps and side panels, Google Chat cards, Meet stages |  
| MCP Apps hosts | Claude, ChatGPT, Gemini Enterprise and other hosts that display MCP Apps views |  ``
| Android | Google's androidx.a2ui Jetpack Compose renderer plus the atomic-catalog library |
| Claude Code | a plugin that draws atoms in terminal panes |
| Email and PDF | static renders for the atoms that suit them |

Each [surface page](https://a2uicatalog.ai/surfaces/android/) lists exactly which components work there.

## A2UI and MCP

They do different jobs and work together. MCP connects a model to tools and data. A2UI describes interface. An MCP tool can return an A2UI surface, so an agent that uses MCP can also show UI.

MCP Apps is the closer comparison. As a2ui.org puts it, MCP Apps "treat UI as a resource": a server provides pre-built HTML that the host shows in a sandboxed frame. A2UI instead sends component blueprints and leaves styling and rendering to the host. The two combine well: the catalog's renderer runs inside an MCP Apps view, so one A2UI payload reaches every MCP Apps host. There's more on this in [MCP Apps isn't A2UI's competitor](https://a2uicatalog.ai/blog/007-mcp-apps-portability/).

## A2UI and AG-UI

The names give it away. A2UI is about the user **interface**: which components to show and what data they hold. AG-UI, the [Agent–User Interaction protocol](https://docs.ag-ui.com/introduction), is about the **interaction**: the live connection between an agent backend and an app, carrying messages, tool calls, state updates and the user's actions as a stream of events.

They stack rather than compete. An A2UI surface can travel inside an AG-UI stream; CopilotKit, for example, sends it as an `ActivitySnapshot` event. As a2ui.org puts it, "use AG-UI as the pipe, A2UI as the content." The film above shows the same thing: AG-UI is one of the pipes, and the A2UI letter rides inside it.

## Get started

1. **Browse** the [catalog](https://a2uicatalog.ai/) and open any atom to see its fields and a live preview.
2. **Try it** in an MCP host: add the a2uicatalog MCP server, ask for a dashboard, and the host renders it.
3. **Render it yourself** on the web, in Apps Script, or on Android with `implementation("ai.a2uicatalog:atomic-catalog:0.1.0")`.

## FAQ

### Is A2UI a Google project?

Google created it, with contributions from CopilotKit and the open-source community, and it is developed in the open at [github.com/a2ui-project/a2ui](https://github.com/a2ui-project/a2ui). The A2UI Atomic Catalog is an independent open-source catalog built on it.

### Does the agent generate HTML?

No. It sends JSON that names components. The renderer draws them with code the app trusts.

### What happens if an agent asks for a component the app doesn't have?

That depends on the renderer. Google's Android renderer refuses unknown types, so the catalog's emitter reads which catalogs an app supports and sends a simpler version to apps that lack them.

### Which AI models can use it?

Any model that can produce JSON. The catalog's MCP server and per-atom JSON Schemas help models produce valid payloads.

### Is it free?

Yes. The protocol is Apache 2.0, and the A2UI Atomic Catalog is MIT-licensed.

### How is A2UI different from AG-UI?

A2UI describes the user interface. AG-UI, the Agent–User Interaction protocol, carries the interaction between an agent and an app: messages, tool calls, state and user actions. A2UI often travels over AG-UI; as a2ui.org puts it, "use AG-UI as the pipe, A2UI as the content."

Independent, unofficial catalog: not affiliated with, endorsed by, or sponsored by Google or Anthropic. A2UI is Google's protocol; MCP is Anthropic's. Maintained by [Curtis Krygier](https://www.linkedin.com/in/curtiskrygier). MIT License.
