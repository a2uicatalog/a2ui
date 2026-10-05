# atomic-catalog for Android (ai.a2uicatalog:atomic-catalog)

The a2uicatalog atom catalog for Google's A2UI Compose renderer
(`androidx.a2ui` 1.0.0-alpha01). Add one dependency and an agent can use every atom in
the catalog on Android.

## Install

Published on Maven Central. Needs `androidx.a2ui` 1.0.0-alpha01 (Kotlin 2.2.20, Compose 1.13).

```kotlin
dependencies {
    implementation("ai.a2uicatalog:atomic-catalog:0.1.0")
}
```

## Use

```kotlin
val catalog = A2uiAtomicCatalog.catalog(context)
val processor = A2uiMessageProcessor(listOf(catalog))
```

Spec versions: renders A2UI **v0.9 / v0.9.1** messages (what `androidx.a2ui` accepts).
v1.0 payloads are converted to v0.9 by `A2uiAtomicCatalog.adapt()` (see below).

## How it draws

- **Basic Catalog components** (Text, Column, Row, Card, Button, Divider, Image) draw
  natively in Compose. `androidx.a2ui` ships their definitions but no drawing code, so
  the library includes `defaultBasicComponents`. Pass your own to
  `A2uiAtomicCatalog.catalog(context, basicComponents = ...)` to use your design system.
- **Every stable catalog atom** is registered and draws through a WebView bridge running
  the catalog's own web renderer. `androidx.a2ui` throws on any unregistered
  component type, so nothing may be missing.
- **Films** (`motion_timeline`) arrive as one component and play as one stage.

The atom list (`atoms.json`) and the renderer (`renderer-bundle.html`) are generated
at build time from this checkout's `atoms/schema.yaml` and
`public/surfaces/mcp-apps/renderer-bundle.html` (`tools/gen_android_assets.py`). They are
never copied into git, so an AAR always matches the catalog it was built from.

## Agents and capabilities

`androidx.a2ui` tells the agent which catalogs the app registered
(`a2uiClientCapabilities.supportedCatalogIds`). The catalog's emitter
(`renderers/a2ui_v1.emit_messages`) reads that:

- **App uses this library:** full surfaces, sent as v0.9 messages.
- **Stock app, Basic Catalog only:** Basic Catalog components only. Each atom becomes
  a Text with its readable text, so the app never sees a type it can't draw.

`A2uiAtomicCatalog.adapt()` is a safety net for payloads not emitted for this renderer: it
rewrites v1.0 to v0.9, splits createSurface/updateComponents, and turns unknown types
into a visible placeholder.

## Build

Needs JDK 17, the Android SDK (platform 37.1) and `python3` with PyYAML.

    ./gradlew :a2ui-atoms:assembleRelease     # -> a2ui-atoms/build/outputs/aar/

The demo and test app (`a2ui-private/android-viewer`) uses this library through a
Gradle composite build.

## Status and limits

- Release builds (the published AAR) register stable atoms only; preview atoms stay in
  the repo. Debug builds register every atom, so the viewer can test previews.

- Version 0.1.0, published on Maven Central (`ai.a2uicatalog:atomic-catalog`).
- Consecutive bridged atoms in a Column share one WebView (one renderer load per run
  instead of one per atom); a lone bridged atom gets its own.
- `ops.py run android-build` builds the AAR and verifies it: its atoms must equal
  `atoms/schema.yaml` and its renderer bundle must be byte-identical to the web one.
- Tested on a Pixel 7 Pro (Android 17) with samples covering Basic Catalog, bridged
  atoms, WebGL brick models, films and stock-client surfaces.
