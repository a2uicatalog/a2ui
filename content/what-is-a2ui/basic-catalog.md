---
title: "A2UI Basic Catalog: @@BASIC_N@@ Components and @@BASIC_FN@@ Functions"
date: 2026-11-14
summary: "What the A2UI Basic Catalog contains and what you can do with it: show, arrange, input, bind data, format. With what we have and have not tested."
read_minutes: 4
---

# A2UI Basic Catalog: what it contains and what you can do with it

The Basic Catalog is the set of components and functions A2UI ships with: @@BASIC_N@@ components and @@BASIC_FN@@ functions in the v1.0 catalog. A renderer that supports it can draw any surface built from it, with no custom code in the host. This page lists what is in it, grouped by what you can do, and says plainly how much of it we have tested.

## What is in the Basic Catalog

The components are @@BASIC_COMPONENT_NAMES@@. The functions are @@BASIC_FUNCTION_NAMES@@. Both lists are read from the Basic Catalog file in the v1.0 specification.

## What you can do with it

- **Show content:** Text, Image, Icon, Video and AudioPlayer.
- **Arrange content:** Row, Column, List, Card, Tabs, Modal and Divider. Row, Column and List can repeat their children from a data list.
- **Take and check input:** Button, TextField, CheckBox, ChoicePicker, Slider and DateTimeInput. All six accept validation checks.
- **Bind to live data:** any property can take a data binding or a function call.
- **React to the user:** a Button fires an action to the agent.
- **Compute and format:** the functions: `and`, `or`, `not`; `formatCurrency`, `formatDate`, `formatNumber`, `formatString`, `pluralize`; `email`, `length`, `numeric`, `regex`, `required`; and `openUrl`.

## What we have tested

Of the @@BASIC_N@@ components we have tested five: Text, Image, Button, Card and Column. We have not tested any of the functions. The rest is what the specification allows, not something we have measured.

What we did test: a picture drawn on the server and shown in a Basic Image drew and animated on the official React renderer and in one Gemini Enterprise trial, with no custom catalog. The full measurements, with the message sizes for the same game built four ways, are in our article [A2UI: How basic is the basic catalog?](/blog/022-a2ui-how-basic-is-the-basic-catalog/).

## How far can Basic go?

It goes further than the name suggests, and it has clear limits. A drawn Image can show a chart, a board or a simple animation, but it is a picture: no hover, no zoom and no partial updates. For those you need a custom catalog. [How to make an A2UI custom catalog](/what-is-a2ui/custom-catalog/how-to/) walks through making one, and [the worked example](/what-is-a2ui/custom-catalog/) shows ours.

## FAQ

### What is the A2UI Basic Catalog?

It is the standard catalog of components and functions that A2UI defines, so any renderer that supports it can draw any surface built from it with no custom code. It has @@BASIC_N@@ components and @@BASIC_FN@@ functions in v1.0.

### What components does the Basic Catalog have?

@@BASIC_COMPONENT_NAMES@@.

### What functions does the Basic Catalog have?

@@BASIC_FUNCTION_NAMES@@. They format values for display, check input and combine conditions, and `openUrl` opens a link.

### Can you draw charts with only the Basic Catalog?

Not with a component: there is no chart in it. In our tests, a picture drawn on the server and shown in a Basic Image worked as a static picture or a simple animation on the official React renderer and in one Gemini Enterprise trial. We have not tested it on native renderers such as Flutter or Jetpack Compose.

### Do I need a custom catalog?

Only when a picture is not enough, for example when you need hover, zoom, partial updates or a component with real keyboard behaviour. See [how to make a custom catalog](/what-is-a2ui/custom-catalog/how-to/).

## Get started

- The Basic Catalog in the official docs: [Catalogs on a2ui.org](https://a2ui.org/concepts/catalogs/).
- Our measurements: [A2UI: How basic is the basic catalog?](/blog/022-a2ui-how-basic-is-the-basic-catalog/).
- New to the protocol? Start with [What is A2UI?](/what-is-a2ui/).
