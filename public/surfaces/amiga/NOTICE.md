# Amiga view: third-party notices and provenance

- **vAmigaWeb** (https://github.com/vAmigaWeb/vAmigaWeb), GPL-3.0. A WebAssembly port (by Mithrendal) of **vAmiga**
  (https://github.com/dirkwhoffmann/vAmiga, by Dirk Hoffmann), a cycle-exact Amiga 500/1000/2000 emulator. This is the
  `nonworker` build variant — `thread_type=nonworker` in vAmigaWeb's own `CMakeLists.txt` — which does **not** use
  `WASM_WORKERS`, pthreads, or `SharedArrayBuffer`, confirmed by grepping the shipped `vAmiga.js` for both strings (zero
  matches). Chosen deliberately: this host's MCP Apps view is not cross-origin isolated (measured live, 2026-09-21, via the
  diagram-studio view's host diagnostics), so a build depending on shared-memory threads would not run here at all.

  Vendored, from the project's own built deployment (github.com/vAmigaWeb/vAmigaWeb.github.io), as a **minimal subset**
  (~12 MB, down from the ~41 MB full deployment): the core `vAmiga.js`/`vAmiga.wasm`, the desktop UI's JS/CSS (jquery,
  bootstrap, the `vAmiga_*.js` modules actually referenced by `index.html` — including `vAmiga_audioprocessor.js`, which is
  NOT a static `<script>` tag but a required `audioWorklet.addModule()` target), the icon/sound assets the UI references,
  and only the two ROM files the default boot path (`fetchOpenROMS("aros")`) actually fetches. Dropped: the in-app
  script/config editor (`js/cm6/`, CodeMirror+JSHint, ~1 MB — unneeded, since this view drives boot config itself via the
  URL-fragment convention below, not the in-app editor UI), the debug console (`js/eruda.js`, dynamically loaded only if a
  person opens it — a request for it 404s harmlessly, same pattern as the diagram-studio draw.io viewer's dropped MathJax
  call), `js/jszip.min.js`/`js/dexie.min.js`/`js/virtualjoystick.js` (confirmed zero references anywhere in the files kept),
  `js/vAmigaWeb_player.js` (the project's own "embed via nested iframe" helper — not usable here, since this host's
  frame-src CSP blocks all framing regardless of origin; this view is served as the ui:// view's OWN top-level content
  instead, which is not subject to that restriction), the service worker (`sw.js` + its registration script, stripped from
  `index.html` — inappropriate for a view running inside someone else's page), and a third-party analytics script
  (`cloud.umami.is`, stripped from `index.html` — no reason to phone home from a self-hosted copy), and unused dated ROM
  variants (only `aros-rom-20260820.bin` / `aros-ext-20260820.bin` are kept, the ones the boot path actually requests).

  One small addition: a `ui/initialize` / `ui/notifications/initialized` / `ui/notifications/size-changed` handshake script,
  inserted right after `<head>` (fires in well under a second, independent of the emulator's own — much slower — boot),
  since the upstream project has no notion of the MCP Apps host protocol. Otherwise the vendored files are byte-for-byte
  upstream.

- **AROS** (AROS Research Operating System, https://github.com/aros-development-team/AROS), AROS Public License (APL, an
  open-source MPL derivative). The two `roms/aros-*-20260820.bin` files are AROS's own free, open-source reimplementation
  of Amiga Kickstart, used here BECAUSE Commodore's original Kickstart ROMs remain copyrighted and cannot be bundled — this
  is vAmigaWeb's own documented, explicit position ("commodore kickstarts are still under copyright"), and AROS is its
  explicitly-supported free alternative. No Commodore-copyrighted firmware of any kind is present in this view.

- **`game.adf`**: "Alien Fish Finger" (1996, Skull Army, Blitz BASIC), sourced from the Internet Archive's curated
  "Commodore Amiga - Games - Public Domain - [ADF]" collection (archive.org/details/commodore-amiga-games-public-domain-adf),
  explicitly tagged Public Domain by that collection's own curation. Chosen after a genuine search (2026-09-22) for a
  demoscene alternative with an explicit, formal open license found none with BOTH the technical fit (self-booting,
  OCS/ECS-compatible, ready-to-run disk image) AND clear licensing — the one iconic candidate considered (Spaceballs'
  "State of the Art", 1992) rests on 30+ years of uncontested open hosting on scene.org rather than a stated license, so
  was set aside in favour of this unambiguously-licensed alternative.

Mounted automatically on load via vAmigaWeb's own URL-fragment convention (`index.html#{"AROS":true,"url":"game.adf",...}`
— the same general pattern, JSON in a `#` fragment, as the diagram-studio view's `#R<base64>` draw.io deep link, both
predating and independent of each other), so nothing is fetched from any third party at runtime — everything this view
needs is served from this same origin.
