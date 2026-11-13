---
title: Deploy your Google Apps Script renderer — A2UI Catalog
description: Deploy your own A2UI Google Apps Script renderer in 4 commands. Open source, MIT licensed. You own the URL, you own the deployment.
canonical: https://a2uicatalog.ai/renderer/
generated_by: gen_page_twins.py
---

# Deploy your Google Apps Script renderer — A2UI Catalog

[A2UI Catalog](https://a2uicatalog.ai/) › Deploy your Google Apps Script renderer

# The Google Apps Script renderer

A **Google Apps Script web app you deploy once**, then call with any payload from the catalog. Open source, MIT licensed. You own the URL — no dependency on the demo endpoint.

Try it now — no setup

Three **permanent short links**, rendered live by **MCP Apps on a2uicatalog.ai** — the same sandboxed host, the same renderer source the steps below put in your own Apps Script account. Each demo proves a different capability.

### ATC Ops Deck — live data in a link

A slide playbook over Toulouse-Blagnac: **live ADS-B and METAR feeds**, an isometric takeoff scene, and a fullscreen airspace command deck with a real-time traffic ticker. Everything arrives as one declarative payload — the aircraft on the radar are actually up there right now.

Proves: playbook slides, data-source atoms, fullscreen breakout — in a plain shareable link.

[Open demo →](https://a2uicatalog.ai/s/atc)

```
https://a2uicatalog.ai/s/atc
```

### Americano Night — a wired, interactive app

A padel tournament night as a **wired surface**: live scoring, rotation schedules, standings that update as you tap — state stores, actions, and sessions, still expressed as one declarative payload. Open it on two phones with the same link and score together.

Proves: the wired dialect — real interactivity without the agent writing a line of imperative code.

[Open demo →](https://a2uicatalog.ai/s/americano#t=renderer-demo)

```
https://a2uicatalog.ai/s/americano
```

### Learn A2UI + MCP — the in-depth brief

A five-module curriculum on **A2UI and the Model Context Protocol**: the payload contract, atoms and the graduation pipeline, the `?p=` URL model, MCP fundamentals, and MCP Apps' sandboxed handshake. Flashcards, knowledge checks, and worked examples throughout.

Proves: `module_map` pagination — five module cards, each its own permanently-published page, so depth is unbounded while every link stays shareable. Module 3 explains why: the same atom builds sub-pages differently depending on whether it's rendering on Apps Script or here, in the browser.

[Open demo →](https://a2uicatalog.ai/s/learn-a2ui)

```
https://a2uicatalog.ai/s/learn-a2ui
```

## Deploy your own

Prerequisites: **Node.js 20+** (for `npm`, used to install clasp in step 2) and a Google account.

1

### Clone the repo

The renderer lives in `apps-script-surface/gas-wired-renderer/` — 550 of the catalog's 573 atoms render on Apps Script, no CDN, no external dependencies.

```
# Clone and navigate to the renderer directory
git clone https://github.com/a2uicatalog/a2ui
cd a2ui/apps-script-surface/gas-wired-renderer

```

2

### Authenticate with clasp

clasp is Google's Apps Script CLI. One-time login — uses your Google account to deploy the renderer as a GAS web app.

```
npm install -g @google/clasp
clasp login

```

3

### Create and push

Creates a new GAS project in your Google account and pushes all renderer files. Takes about 30 seconds.

```
clasp create --type webapp --title "My A2UI Renderer"
clasp push

```

4

### Deploy

Deploy as a web app accessible to anyone. You'll get a URL — that's your renderer endpoint.

```
clasp deploy --description "A2UI Renderer v1"
# → https://script.google.com/macros/s/YOUR_ID/exec

```

## What you get

🔒

#### You own the deployment

Runs in your Google account. No dependency on the catalog's demo URL. Survives any catalog changes.

⚡

#### 550 atoms, ready to go

Stat cards, charts, globes, animations, tables, forms — all render immediately. A handful of data-source atoms want their own API key (see below) and degrade gracefully without one.

🎨

#### Fully customisable

Fork the renderer, add your own atoms, change the CSS, restrict to specific surfaces. It's your code.

🔄

#### Stay up to date

Pull the latest from the repo and `clasp push` again when new atoms are added to the catalog.

## Protocol support

The renderer accepts **A2UI v1.0**: a `createSurface` message with its `components` and `dataModel` inline, one surface per link. It draws all 18 components of the v1.0 Basic Catalog (AudioPlayer, Button, Card, CheckBox, ChoicePicker, Column, DateTimeInput, Divider, Icon, Image, List, Modal, Row, Slider, Tabs, Text, TextField, Video), binds inputs to the data model, and sends a Button's `action` event to the `a2uiAction` function in your project's `Code.gs`. It also accepts the catalog's own `blocks` format, shown further down.

Not supported: A2UI v0.9 and v0.8 input, and incremental `updateComponents`, `updateDataModel` or `deleteSurface` messages on a link.

```
// A minimal A2UI v1.0 surface: a text, a bound input and a button that sends an event
function doGet() {
  const message = {
    "version": "1.0",
    "createSurface": {
      "surfaceId": "hello",
      "catalogId": "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json",
      "dataModel": {"form": {"name": ""}},
      "components": [
        {"id": "root", "component": "Column", "children": ["title", "name", "go"]},
        {"id": "title", "component": "Text", "text": "Hello from Apps Script"},
        {"id": "name", "component": "TextField", "label": "Your name", "value": {"@path": "/form/name"}},
        {"id": "go", "component": "Button", "variant": "primary", "child": "go-label", "action": {"event": {"name": "greet", "context": {"who": {"@path": "/form/name"}}}}},
        {"id": "go-label", "component": "Text", "text": "Say hello"}
      ]
    }
  };

  const p = Utilities.base64EncodeWebSafe(
    Utilities.newBlob(JSON.stringify(message)).getBytes()
  );
  const url = "https://script.google.com/macros/s/YOUR_ID/exec?p=" + p;

  return HtmlService.createHtmlOutput(
    '<script>window.location="' + url + '"</script>'
  );
}

```

## Call it from your GAS project

Once deployed, use your renderer URL with any payload from the catalog.

```
// In any GAS project — call your renderer with atom blocks
function doGet() {
  const blocks = [
    { type: "stat_card", value: "1,234", label: "Daily users", delta: "+12%", is_up: true },
    { type: "progress_bar", value: 75, label: "Q2 target" },
    { type: "globe_3d", theme: "earth", size: 300 }
  ];

  const payload = Utilities.base64EncodeWebSafe(
    Utilities.newBlob(JSON.stringify(blocks)).getBytes()
  );
  const url = "https://script.google.com/macros/s/YOUR_ID/exec?p=" + payload;

  return HtmlService.createHtmlOutput(
    '<script>window.location="' + url + '"</script>'
  );
}

```

 **The "Try it live" button on each atom page** uses the catalog's shared demo renderer — same code, same atoms. It's there so you can explore without deploying. For production use, deploy your own.

 **A few atoms want their own Script Properties** — Trading212 (`T212_API_KEY`, `T212_API_SECRET`), Twelve Data (`TWELVE_API_KEY`) and Vertex AI (`VERTEX_PROJECT_ID`) each back one data-source atom. Set them under **Project Settings → Script Properties** in your Apps Script editor if you use those atoms; every other atom works with none set, and these three fail gracefully (return an explicit error, not a broken page) without their key.

[Browse atoms →](https://a2uicatalog.ai/) [View source on GitHub](https://github.com/a2uicatalog/a2ui/tree/main/apps-script-surface/gas-wired-renderer) [ARD manifest](https://a2uicatalog.ai/.well-known/ai-catalog.json)
