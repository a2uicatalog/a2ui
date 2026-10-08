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

- **All 18 Basic Catalog components** draw natively in Compose. By default the library
  uses Google's own Material 3 versions from `androidx.compose.material3:material3-a2ui`
  (`A2uiAtomicCatalog.materialBasicComponents()`), except Image, Video and AudioPlayer:
  Google's take a media renderer from the app, so the library brings its own (Video and
  AudioPlayer open in the device's player). `defaultBasicComponents` is the library's own
  full set of 18, matching the web renderer's look. The engine binds each input's value to
  the data model, so a Button's action sends what the user entered. Pass your own list to
  `A2uiAtomicCatalog.catalog(context, basicComponents = ...)` to use your design system.
- **Keep `material3` at the version `material3-a2ui` pins** (`1.5.0-alpha28` for
  `1.0.0-alpha01`). AndroidX alphas promise no binary compatibility: with `1.5.0-alpha29`
  Google's Slider fails at runtime with `NoSuchMethodError`. If your app needs a newer
  `material3`, pass `defaultBasicComponents` instead.
- **Some catalog atoms draw natively in Compose** (from 0.3.0): `concept_ladder` and
  `concept_rung` (a layered reading: attribution, hero model, rung rail, verbatim-quote
  blocks), with the same design tokens as the web renderer (`palette`, `fonts`, `theme`).
  The ladder's `rungs` are component ids, resolved through the engine like a Column's
  children. `theme_toggle` draws nothing on Android, where the app's theme applies.
  They are `nativeAtomComponents`; to draw them on the bridge instead, use
  `A2uiAtomicCatalog.catalog(context, A2uiAtomicCatalog.materialBasicComponents(), nativeAtoms = emptyList())`. Compose and a
  browser lay text out differently, so they match the web design closely, not pixel for pixel.
- **Every other stable catalog atom** is registered and draws through a WebView bridge running
  the catalog's own web renderer. `androidx.a2ui` throws on any unregistered
  component type, so nothing may be missing.
- **Films** (`motion_timeline`) arrive as one component and play as one stage.
- **Host extras for bridged atoms:** provide `LocalBridgeExtras` (a `BridgeExtras(script, objects)`)
  around the surface to add JavaScript interfaces and a script that runs before each paint in every
  bridge WebView. A film whose page defines `window.A2UIExport = {kinds, run(root, kind, progress)}`
  shows one export button per kind on its control bar; the app supplies the exporter and decides
  where the file goes (a WebView cannot download a `blob:` URL itself).
- **Images can be inline:** the library's Image draws `data:` URIs (base64) as well as URLs,
  so a payload can carry its own pictures. Capped at 5 MB encoded, and downsampled to 2048 px
  on the long side, since the payload is untrusted.
- **Bridged atom fields can be data bindings** (`{"path": "/film/blocks"}`), including
  whole lists, and repaint when the bound data changes, so inputs bound to the same data
  model edit an atom live. A ChoicePicker stores its selection as a list (`["grid"]`); for
  fields that take one string (text or an enum, marked `scalars` in `atoms.json`) the
  bridge passes the single value (`"grid"`), and list fields are left alone.

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
