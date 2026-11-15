---
title: "How to Make an A2UI Custom Catalog"
date: 2026-11-14
summary: "Make an A2UI v1.0 custom catalog step by step: define a component, check it, use it beside Basic, and plan for hosts that lack it."
read_minutes: 9
---

# How to make an A2UI custom catalog

A custom catalog is how you add your own components to A2UI: a stat card, a chart, a weather card, whatever your product needs. This guide builds one from a real component in the A2UI Atomic Catalog (@@ATOMS@@ components), checks it, uses it next to the Basic Catalog on one surface, and covers what to do when a host does not support it. The rules come from the A2UI v1.0 pages as published on 14 November 2026.

## What a custom catalog is for

The Basic Catalog has @@BASIC_N@@ components and @@BASIC_FN@@ functions: text, layout, a few inputs. It has no chart, no timeline and no weather card. When the screen you need is not in it, you can draw a picture on the server (our [Basic Catalog page](/what-is-a2ui/basic-catalog/) shows how far that goes), or you can make a catalog that adds the component itself.

A catalog is the agreement between an agent and a renderer about what can appear on screen. It names every component and function the agent may use, each one something the renderer can draw. The agent sends only what the catalog lists, and a renderer can refuse anything outside it.

## The shape of a catalog

A catalog is one JSON Schema document. This is a complete small one, holding a single component: the real `weather_now` definition from our catalog, with our own extension keys removed.

```json
@@JSON_WEATHER_CATALOG@@
```

Five things to notice:

- **`catalogId`** names the catalog. It is the one thing the meta-schema requires, and the same value is shared by the agent and the renderer. The agent capabilities schema describes these IDs as not resolvable URIs, so nothing has to be served at that address. The official guide's examples use the same value for `$id` and `catalogId`, and its advice is to version the path (`v1/`, `v2/`) when you make a breaking change.
- **`protocolVersion`** says which A2UI version the catalog targets. Set it. `Catalog.from_json` in the Python SDK treats a catalog with no protocol version as 0.9. The catalog provider classes (`InMemoryCatalogProvider`) raise an error instead, so set it.
- **`components`** holds every component, directly at the top level.
- **`functions`** (not used here) holds functions in the same way.
- **`$defs`** must declare `anyComponent`, the union of all your components, and `anyFunction`. When you define no custom functions, `anyFunction` is `{"not": {}}`, as in the example. Shared definitions that components reuse, such as design tokens, go here too.

## Define a component

Each component is a JSON Schema object. In the example above, `weather_now` is declared under `components` with a `component` property whose `const` is its name, plus typed properties. Its values use the shared types from A2UI's `common_types.json` (`DynamicString`, `DynamicNumber`, `DynamicValue`), which is what lets a value be a literal or a binding to the data model.

The rules that matter most when you write one, from the v1.0 pages:

- **Names.** Component, function and property names must be valid Unicode identifiers (UAX #31): they cannot start with a digit, and they can contain no spaces or symbols apart from the underscore.
- **No `Surface`.** The name `Surface` is reserved: do not give a component that name.
- **Top level only.** Declare components directly under `components` and functions directly under `functions`. Never put a component schema inside `$defs`, even wrapped in `allOf`.
- **Flat.** Keep each component a single `type: "object"` with its properties directly on it. Do not use `oneOf`, `anyOf` or a general `allOf` at the component's root.
- **Leave the envelope alone.** The properties every component carries (`id`, `@catalogId`, `@accessibility`, `@metadata`) are added by the protocol envelope, so leave them out of your schema and do not pull them in with `ComponentCommon`.
- **References.** Point at a definition in your own `$defs` with `#/$defs/<Name>`. For the standard types, use the relative form, `common_types.json#/$defs/...`. A reference to anything else outside the catalog is a catalog error, and the loader must report it instead of fetching the target.
- **Accessibility.** If a component or the agent gives an explicit label or description, it wins over whatever the renderer would work out from appearance.

## Define functions and checks

A catalog can also declare functions: pieces of logic the renderer runs on the client, such as formatting a currency or checking an email address. They sit under `functions`, and the same naming rules apply. A function that should run only from a real user gesture, as `openUrl` does in the Basic Catalog, declares `requiresUserActivation: true`. Renderers must then run it only from such a gesture, for example inside an action handler, and never from a passive binding or a validation check. In v1.0 a function can also live on the agent, for server-side work such as checking stock.

## Check it before you ship

Validate the catalog document against the A2UI v1.0 catalog meta-schema, then load it with an SDK. Two checks catch most mistakes:

- **The meta-schema** catches a malformed document, a misplaced component or a missing `catalogId`.
- **The SDK on load** catches more. In the Python SDK, loading a catalog raises an error if the catalog id is missing, if `components` is not an object or a component is not a JSON object, or if a v1.0 document points a `$ref` at any document other than itself or `common_types.json`. Loading does not check that a component's schema is valid JSON Schema; that error appears the first time a message is validated. For v1.0 catalogs it also checks component names against the identifier rule, which is Python's `str.isidentifier()`: a space, a hyphen or a leading digit fails, and Unicode letters pass. The TypeScript SDK checks identifiers the same way on load, and the Dart SDK never fetches a v1.0 `$ref` to another document.

Validation through `validate_payload` is strict by default. In the Python SDK a component the catalog does not define is reported with the code `unrecognized_component`, and a relaxed mode (`allow_unknown_elements`, a field of `ValidationConfig`, also set by `RELAXED_VALIDATION`) exists for renderers that want to tolerate unknown ones. A bare `MessageProcessor` does no component validation unless you give it a `ValidationConfig`.

The Ontology check we ran on 14 November found that the example catalogs in the official v1.0 guide, and the Basic Catalog itself, validate against the live meta-schema. We used an approximation for the Unicode identifier patterns in those runs. The v0.9.1 examples we did not validate.

## Use it on the agent

When a session starts, the renderer sends the catalogs it supports (`supportedCatalogIds`). The agent picks one for each surface in `createSurface`, with `catalogId`. If none of the agent's catalogs is on that list, there is nothing to draw and, according to the concepts page, the agent sends no UI.

In v1.0 a surface can mix catalogs. `createSurface` sets the surface's default catalog, and any component from another supported catalog carries an `@catalogId`. A component with no `@catalogId` is taken to be in the default one. This is a surface our own emitter produced, with its catalog id pointed at the small catalog above: Basic is the default, and the weather card comes from the weather catalog.

**One spelling to watch.** The v1.0 spec writes this key as `@catalogId`, and the surface below uses that form. Python SDK 0.11.0 (the release on PyPI on 15 November 2026) does not accept it: validating this surface with 0.11.0 fails with "Unrecognized component type" and "Unrecognized reserved protocol directive '@catalogId'", and the same surface with the key spelled `catalogId` passes. SDK 0.10.0 predates the change too. Upstream changed the spelling on 11 November 2026 (pull request #4044), after 0.11.0 was released on 10 November, so the spec and upstream's main branch say `@catalogId` while every installable release we looked at says `catalogId`. Main reads both spellings, and we confirmed that by running an upstream checkout from 11 November, but no release contains it yet. If you validate with 0.11.0, use `catalogId` for now. Do not build on the bare spelling for long: an open upstream issue (#4082) plans to remove it once producers emit the `@` names, and another (#4223) asks which npm versions support the new keys. We have not tested how any renderer treats either spelling.

```json
@@JSON_WEATHER_SURFACE@@
```

In v0.9.1 this is not possible: each surface is locked to one `catalogId` for its lifetime.

The SDK uses the catalog twice. It builds the model's system prompt from the catalog, and it validates what the model sends back. If the renderer names catalog IDs the agent does not hold, the agent ignores them.

**When the host does not support your catalog.** The protocol gives you no fallback: the agent sends nothing. Falling back to Basic is a choice you build. Ours is to read what the host supports and send a Basic-only design when it lacks our catalog. Our emitter can translate a custom surface down to Basic automatically. In a test on 5 November 2026 (the official React renderer 0.15.0, one game), that translation dropped the board and no move could be played. What worked was reading the host's supported catalogs first and sending the Basic design from the start.

## Use it on the renderer

On the renderer side, build the component in your UI framework, give it a catalog with the same `catalogId`, and register that catalog next to the Basic Catalog when you create the message processor. Both sides must hold the same `catalogId`, or the agent will never pick it. We have not checked each framework's registration API for this guide, so follow your framework's A2UI renderer documentation for the exact calls.

## Publish and version

Keep the catalog document somewhere people can read it. Ours is published as [our catalog document](/catalogue/a2ui-atoms-v1.json). Version the path in the `catalogId` when you make a breaking change, and keep old versions working for hosts that have not moved.

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

The rules come from the A2UI v1.0 pages as published on 14 November 2026, and the SDK facts from the Python SDK read at one upstream commit, with the TypeScript and Dart load rules. On 15 November 2026 we ran the Python SDK statements against `a2ui-agent-sdk` 0.11.0 with `a2ui-core` 0.6.0, the releases on PyPI that day. Of eight checks, the wording held for four as written, needed tightening for three (now corrected above), and failed for one, the `@catalogId` spelling. We did not run the TypeScript or Dart SDKs, any newer release, prompts built from two catalogs at once, or any renderer. We have not checked how each framework registers a component, or the Swift and Kotlin SDKs.

## Get started

- [Our catalog document](/catalogue/a2ui-atoms-v1.json) (`catalogId` `@@CATALOG_ID@@`).
- A worked example with the real files: [A2UI custom catalog: a worked example](/what-is-a2ui/custom-catalog/).
- What the Basic Catalog already gives you: [A2UI Basic Catalog](/what-is-a2ui/basic-catalog/).
- The official guide to defining a catalog, for the version of this topic that A2UI's own authors keep current: [Defining a catalog on a2ui.org](https://a2ui.org/guides/defining-a-catalog/).
- New to the protocol? Start with [What is A2UI?](/what-is-a2ui/).
