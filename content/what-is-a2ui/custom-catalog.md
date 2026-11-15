---
title: "A2UI Custom Catalog: a Worked Example with @@ATOMS@@ Components"
date: 2026-11-14
summary: "A real A2UI v1.0 custom catalog, end to end: the catalog document, one component definition, and a surface that mixes it with the Basic Catalog. @@ATOMS@@ components, open source."
read_minutes: 6
---

# A2UI custom catalog: a worked example

A catalog is the contract between an agent and a renderer: the components and functions the
agent may use, and the renderer knows how to draw. A2UI ships one, the
[Basic Catalog](https://a2ui.org/concepts/catalogs/) of @@BASIC_N@@ components. A custom
catalog adds your own. This page walks through a real one, the A2UI Atomic Catalog, with
@@ATOMS@@ components, using the files it actually publishes.

## What a custom catalog is

In the words of [a2ui.org](https://a2ui.org/concepts/catalogs/), a catalog "is a collection of
components and functions that acts as a contract between an agent and a renderer." The renderer
lists the catalogs it supports (`supportedCatalogIds`) when a session starts; the agent picks one
as the surface default with `catalogId` in `createSurface`.

Since v1.0, a surface can also mix catalogs. Any component can name its own catalog with
`@catalogId`, so a surface can take its layout from the Basic Catalog and drop in components
from yours. That is how this catalog is meant to be used.

For a step-by-step build of your own, see [How to make an A2UI custom catalog](/what-is-a2ui/custom-catalog/how-to/).
For what the Basic Catalog already gives you, see [A2UI Basic Catalog](/what-is-a2ui/basic-catalog/).

## The catalog document

A v1.0 catalog is one JSON Schema document. Its `catalogId` is an identifier shared by the agent and the renderer; this one is also the address the file is served from. This is the top of the one this site publishes at
[`/catalogue/a2ui-atoms-v1.json`](/catalogue/a2ui-atoms-v1.json), with the component list cut
short:

```json
@@JSON_CATALOG_HEAD@@
```

The document also carries `instructions`: Markdown that an agent SDK adds to the model's system
prompt, here telling the model how to compose these components with Basic Catalog containers.

## One component definition

Each key under `components` is a component name; its schema is the field contract. This is
`stat_card` as published, less its two routing keys (`x-routing-text`,
`x-intent-phrases`):

```json
@@JSON_STAT_CARD@@
```

The fields use the shared types from the A2UI spec (`DynamicString`, `DynamicBoolean`), so any
of them can be a literal or bound to the data model with `{"@path": ...}`.

## Using it alongside the Basic Catalog

The surface below sets the Basic Catalog as its default and gives the one component from this
catalog its own `@catalogId`. The `Column` and `Text` come from the Basic Catalog; `stat_card`
comes from this one. It is the output of the same emitter that serves this site's surfaces, and
the repository's tests check it against the official v1.0 schema and against the `stat_card`
definition above, then render it.

```json
@@JSON_MIXED_EXAMPLE@@
```

`metadata.extensions` is the spec's extension point for a surface's own data. A renderer has to
list this catalog in `supportedCatalogIds` before an agent may send it these components; for a
renderer that supports only the Basic Catalog, the emitter sends a Basic-only version of the
surface instead.

## Beyond the spec: where each component works

The spec lets a catalog add its own keys. This one adds two to every component:

- `x-surfaces`: where the component works, from web pages to Google Chat, email, PDF and slides.
- `x-renderers`: which renderers draw it, measured, with evidence and dates in
  [`renderer-matrix-v1.json`](/catalogue/renderer-matrix-v1.json).

Measured today, these web renderers draw this many of the @@ATOMS@@ components:

@@WEB_RENDERER_TABLE@@

## A design choice: alongside, not a superset

A common way to build a custom catalog is to include the whole Basic Catalog in it, so the
custom catalog is a superset. This one does not. It holds only its own components and leaves
layout, text and inputs to the Basic Catalog, joined on the surface by `@catalogId`. The Basic
Catalog stays exactly as Google publishes it, renderers load the two catalogs separately, and
a surface names which catalog each component comes from.

## Get started

- The catalog document: [`/catalogue/a2ui-atoms-v1.json`](/catalogue/a2ui-atoms-v1.json)
  (`catalogId` `@@CATALOG_ID@@`).
- Every component with its live preview: [the catalog](/).
- The MCP server agents use to find and render components: `https://a2uicatalog.ai/mcp`.
- New to the protocol? Start with [What is A2UI?](/what-is-a2ui/).
