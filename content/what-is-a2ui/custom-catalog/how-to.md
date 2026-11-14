---
title: "How to Make an A2UI Custom Catalog"
date: 2026-11-14
summary: "Make an A2UI v1.0 custom catalog step by step: define a component, check it, use it beside Basic, and handle hosts that lack it. Real weather card."
read_minutes: 9
---

# How to make an A2UI custom catalog

A custom catalog is how you add your own components to A2UI: a stat card, a chart, a weather card, whatever your product needs. This guide builds one from a real component in the A2UI Atomic Catalog (@@ATOMS@@ components), checks it, uses it next to the Basic Catalog on one surface, and covers what to do when a host does not support it. The rules come from the A2UI v1.0 pages as published on 14 November 2026.

## What a custom catalog is for

The Basic Catalog has @@BASIC_N@@ components and @@BASIC_FN@@ functions: text, layout, a few inputs. It has no chart, no timeline and no weather card. When the screen you need is not in it, you can draw a picture on the server (our [Basic Catalog page](/what-is-a2ui/basic-catalog/) shows how far that goes), or you can make a catalog that adds the component itself.

A catalog is a contract between an agent and a renderer. It lists the components and functions the agent may use and the renderer knows how to draw. The agent can only send what the catalog allows, and a renderer can reject anything it does not know.

## The shape of a catalog

A catalog is one JSON Schema document. This is a complete small one, holding a single component: the real `weather_now` definition from our catalog, with our own extension keys removed.

```json
@@JSON_WEATHER_CATALOG@@
```

Five things to notice:

- **`catalogId`** names the catalog. It is the one thing the meta-schema requires, and the same value is shared by the agent and the renderer. The agent capabilities schema describes these IDs as not resolvable URIs, so nothing has to be served at that address. The official guide's examples use the same value for `$id` and `catalogId`, and its advice is to version the path (`v1/`, `v2/`) when you make a breaking change.
- **`protocolVersion`** says which A2UI version the catalog targets. Set it. The Python SDK treats a catalog with no protocol version as 0.9.
- **`components`** holds every component, directly at the top level.
- **`functions`** (not used here) holds functions in the same way.
- **`$defs`** holds shared definitions, such as design tokens, that components can reference.

## Define a component

Each component is a JSON Schema object. In the example above, `weather_now` is declared under `components` with a `component` property whose `const` is its name, plus typed properties. Its values use the shared types from A2UI's `common_types.json` (`DynamicString`, `DynamicNumber`, `DynamicValue`), which is what lets a value be a literal or a binding to the data model.

The rules that matter most when you write one, from the v1.0 pages:

- **Names.** Component names, function names and property names must follow the Unicode identifier rules (UAX #31): no leading digit, no whitespace, no symbols other than the underscore.
- **No `Surface`.** A catalog must not define a standard component named `Surface`.
- **Top level only.** Components and functions go directly under `components` and `functions`. A component schema must not be defined inside `$defs`, even in an `allOf` wrapper.
- **Flat.** A component is a single `type: "object"` with its properties directly on it. No `oneOf`, `anyOf` or non-trait `allOf` at the component root.
- **Do not wrap the envelope.** The shared properties every component carries (`id`, `@catalogId`, `@accessibility`, `@metadata`) are added by the protocol envelope. Do not add them yourself with `ComponentCommon`.
- **References.** A property can point at a catalog-scoped definition with `#/$defs/<Name>`. A reference to the standard types must use the relative form, `common_types.json#/$defs/...`. A reference to anything else outside the catalog is an error: an implementation must report a catalog error and must not fetch it over the network.
- **Accessibility.** If a component or the agent supplies an explicit accessibility label or description, it must override what the renderer would infer from how the component looks.

## Define functions and checks

A catalog can also declare functions: pieces of logic the renderer runs on the client, such as formatting a currency or checking an email address. They sit under `functions`, and the same naming rules apply. A function that opens something on the user's device, as `openUrl` does in the Basic Catalog, should be marked `requiresUserActivation: true`. A renderer must then run it only from a real user gesture, such as inside an action handler, and never from a passive binding or a validation check. In v1.0 a function can also live on the agent, for server-side work such as checking stock.

## Check it before you ship

Validate the catalog document against the A2UI v1.0 catalog meta-schema, then load it with an SDK. Two checks catch most mistakes:

- **The meta-schema** catches a malformed document, a misplaced component or a missing `catalogId`.
- **The SDK on load** catches more. In the Python SDK, loading a catalog raises an error if the catalog id is missing, if the document is malformed, or if a v1.0 document points a `$ref` at any document other than itself or `common_types.json`. For v1.0 catalogs it also checks component names against the identifier rule. The TypeScript SDK checks identifiers the same way on load, and the Dart SDK never fetches a v1.0 `$ref` to another document.

Validation is strict by default. In the Python SDK a component the catalog does not define is reported with the code `unrecognized_component`, and a relaxed mode (`allow_unknown_elements`) exists for renderers that want to tolerate unknown ones.

The Ontology check we ran on 14 November found that the example catalogs in the official v1.0 guide, and the Basic Catalog itself, validate against the live meta-schema. We used an approximation for the Unicode identifier patterns in those runs. The v0.9.1 examples we did not validate.

## Use it on the agent

When a session starts, the renderer sends the catalogs it supports (`supportedCatalogIds`). The agent picks one for each surface in `createSurface`, with `catalogId`. If none of the agent's catalogs match, the protocol says the agent sends no UI.

In v1.0 a surface can mix catalogs. `createSurface` sets the surface's default catalog, and any component from another supported catalog carries an `@catalogId`. A component with no `@catalogId` is taken to be in the default one. This is a surface our own emitter produced: Basic is the default, and our weather card comes from our catalog.

```json
@@JSON_WEATHER_SURFACE@@
```

In v0.9.1 this is not possible: each surface is locked to one `catalogId` for its lifetime.

The SDK uses the catalog twice. It builds the model's system prompt from the catalog, and it validates what the model sends back. If the renderer names catalog IDs the agent does not hold, the agent ignores them.

**When the host does not support your catalog.** The protocol gives you no fallback: the agent sends nothing. Falling back to Basic is a choice you build. Ours is to read what the host supports and send a Basic-only design when it lacks our catalog. We tried translating a custom game to Basic by hand in a test on 5 November 2026 (an earlier renderer, one game): the board was dropped and no move could be played. Choosing the Basic design up front, from the host's list, is what worked.

## Use it on the renderer

On the renderer side you implement the component in your UI framework, wrap it in a catalog with the same `catalogId`, and register it alongside the Basic Catalog when you set up the message processor. Both sides must hold the same `catalogId`, or the agent will never pick it. We have not checked each framework's registration API for this guide, so follow your framework's A2UI renderer documentation for the exact calls.

## Publish and version

Keep the catalog document somewhere people can read it. Ours is published at [`/catalogue/a2ui-atoms-v1.json`](/catalogue/a2ui-atoms-v1.json). Version the path in the `catalogId` when you make a breaking change, and keep old versions working for hosts that have not moved.

## FAQ

### What is an A2UI custom catalog?

A catalog is a JSON Schema document that lists the components and functions an agent may use and a renderer knows how to draw. A custom catalog is one you make yourself, to add components the Basic Catalog does not have.

### Do I need a custom catalog?

Not always. The Basic Catalog covers text, layout and a few inputs, and a picture drawn on the server can go a long way. Make a custom catalog when you need a real component, for example one with keyboard behaviour or hover, or messages that stay small.

### Can one surface use the Basic Catalog and my own?

In v1.0, yes. The surface's default catalog is set in `createSurface`, and a component from another supported catalog carries an `@catalogId`. In v0.9.1 a surface is locked to a single catalog.

### What happens if a host does not support my catalog?

The protocol says the agent sends no UI if none of its catalogs match. Falling back to a Basic design is something you build: read the host's supported catalogs and choose.

### How do I check my catalog is valid?

Validate it against the v1.0 catalog meta-schema, then load it with an SDK, which also checks identifiers and references on load. Test a surface that uses it against a renderer that has it registered.

## What this guide covers

The rules come from the A2UI v1.0 pages as published on 14 November 2026, and the SDK facts from the Python SDK read at one upstream commit, with the TypeScript and Dart load rules. None of the SDK behaviour was run for this guide. We have not checked how each framework registers a component, or the Swift and Kotlin SDKs.

## Get started

- The catalog document: [`/catalogue/a2ui-atoms-v1.json`](/catalogue/a2ui-atoms-v1.json) (`catalogId` `@@CATALOG_ID@@`).
- A worked example with the real files: [A2UI custom catalog: a worked example](/what-is-a2ui/custom-catalog/).
- What the Basic Catalog already gives you: [A2UI Basic Catalog](/what-is-a2ui/basic-catalog/).
- The official guide to defining a catalog, for the version of this topic that A2UI's own authors keep current: [Defining a catalog on a2ui.org](https://a2ui.org/guides/defining-a-catalog/).
- New to the protocol? Start with [What is A2UI?](/what-is-a2ui/).
