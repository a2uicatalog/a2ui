# A2UI Thoughts — Working Notes

Private scratch pad. Gitignored. Add anything pertinent here when it comes up for the first time.

---

## Catalog Scaling & Context Bloat

**Problem:** As the catalogue grows to 300-500+ atoms, naive full-schema injection into agent prompts becomes expensive. At 100 atoms ~8-12k tokens; at 500 ~50k tokens — starts competing with actual conversation.

**The spec's answer (v0.8 §Catalog Negotiation):**
The catalog is compiled knowledge, not per-turn injection. `catalogId` in `beginRendering`/`createSurface` is a shared dictionary reference — the agent already knows what `stat_card` means, it doesn't re-describe it each turn. `inlineCatalogs` is the escape hatch for local dev only.

**Three-tier retrieval model:**

| Tier | What | Tokens | Infrastructure |
|---|---|---|---|
| Runbook | Known trigger → pre-mapped atom sequence | 0 | None |
| Compact index | `type: compact_description` for all atoms, always in context | ~1-2k | None |
| Vector retrieval | Embed intent → nearest-neighbor atoms → fetch full spec for top-k | ~0 overhead | Pre-computed embeddings |
| Full spec | Only for selected atoms, on demand | ~200/atom × k | None |

**Vector approach:** At 500 atoms, no dedicated vector DB needed. Pre-compute embeddings once, store as numpy array (~3MB). Cosine similarity at query time is microseconds.

```python
scores = np.dot(query_embedding, catalog_embeddings.T)
top_k = np.argsort(scores)[-5:]
```

Only move to Vertex AI Vector Search at 10k+ items or multi-tenant scale.

**`compact_description` field:** Added to all 101 atoms in schema.yaml (June 2026). Intent-focused, 8-12 tokens, optimised for both embedding quality and human readability. Not rendering detail — semantic intent. Example: `"single KPI value with label delta and accent colour"` not `"div with flex column"`.

---

## Catalog-as-Vocabulary / Runbook Pattern

The catalog defines verbs the agent speaks. `stat_card`, `progress_bar`, `callout` are vocabulary items — client knows how to render each without being told every turn.

**Generative path:** Agent reasons which atoms fit open-ended intent. Needs compact index + possibly vector retrieval. Token-heavy for novel tasks.

**Runbook path:** Pre-mapped keyword → atom sequence. `"sprint_review"` → `[stat_card(velocity), stat_card(bugs), table(backlog), progress_bar(completion)]`. Zero retrieval, zero deliberation. Covers ~80% of real sessions.

**Hybrid path:** Runbook fixes the layout shape, agent fills values from live context. Most powerful pattern for Meet — consistent structure, live data.

**Scaling insight:** At 500 atoms + 50 runbooks, most real sessions never touch generative retrieval. Catalog size stops mattering for common cases.

---

## Multi-LLM Scraping / Format Conversion Pipeline

*(June 2026)*

Use non-CLI LLMs (Perplexity, etc.) as a scraping + format-conversion tier to reduce token burden on the primary agent:

1. **Perplexity scrapes** structured info (UIverse atom specs, GitHub component APIs, design system docs)
2. **Prompt asks for transformation** to a specific target format (schema.yaml atom block, compact_description, surface compatibility flags)
3. **Result lands in repo** ready for validation — no raw scraping noise in primary context

This offloads the "find and parse" work to a model with live web access, keeps the primary agent context clean. The format prompt is the contract — the output must validate against schema.yaml.

---

## Catalog URI (To Do)

Publish `gdm-v0.2.json` at a stable URI so clients can declare it in `supportedCatalogIds`. Candidates:
- `https://a2ui.krygier.fr/catalogue/gdm-v0.2.json`
- Or via the a2ui-catalogue GitHub Pages

`inlineCatalogs` stays as escape hatch for local dev and experimental atoms.

---

## Meet Stage Atom Shortlist (June 2026)

Reviewed the full 170-atom catalogue against Meet stage use cases. 26 atoms identified as specifically relevant:

**Data & Metrics:** `chartjs_bar`, `chartjs_line`, `metric_comparison_card`, `mini_sparkline_set`, `uptime_timeline`
**Content Structure:** `tabs`, `table`, `key_takeaways`, `badge_group`, `before_after`, `file_tree`, `prerequisite_checklist`
**Technical:** `cli_command`, `http_request_block`, `keyboard_shortcut`, `api_param_table`, `api_reference`
**Media:** `carousel`, `diagram`, `color_swatch_grid`, `gallery`, `image_pair`, `video_pair`, `youtube`
**Social/Bio:** `author_bio_card`
**Embeds:** `embed_google_slides` (feasible for public decks; see note below)

**`embed_google_slides` on stage:** Works if presentation is publicly shared (no sign-in required). In live Meet sessions it's somewhat redundant vs screenshare — the value is pairing a data-driven slide *alongside* other stage panels in a split layout. CSP `frame-src` for `docs.google.com` is already unlocked in the local stage server.

Renderer fixes applied (June 2026): `key_takeaways` (items vs points field), `color_swatch_grid` (was hardcoded), `chartjs_bar`/`chartjs_line` (now use real data + SVG), `metric_comparison_card` (real delta calc), `mini_sparkline_set` (real data + SVG), `uptime_timeline` (probabilistic uptime blocks), `author_bio_card` (image field aliasing).

---

## Playbook Creator Skill — Design Intent (June 2026)

The outline demo playbook is a fixed-brief artefact. The next step is a skill that takes *any* meeting brief and produces a stage-ready playbook.

**Mental model:** Brief → agent reasons over catalogue vocabulary → selects atoms → generates slide sequence → fires to stage

**The catalogue is the vocabulary. Playbook YAML is the grammar.**

Pre-mapped patterns (runbook path — zero deliberation):
- Sprint review → `stat_card` (velocity, bugs) + `progress_bar` + `table` (backlog) + `chartjs_line` (burn-down)
- Architecture session → `diagram` + `file_tree` + `http_request_block` + `before_after`
- Team standup → `author_bio_card` per person + `prerequisite_checklist` (blockers) + `badge_group` (status)
- Demo/launch → `carousel` + `video_pair` + `metric_comparison_card` + `uptime_timeline`

**Skill layers:**
1. Atom index — which atoms work on stage, what data they need, surface compatibility
2. Runbook templates — pre-mapped brief types (covers ~80% of real sessions)
3. Generative path — for novel briefs, agent selects atoms + data sources + slide order

This is the catalogue-as-vocabulary / runbook pattern from A2UI spec v0.8 applied to the Meet stage. The skill lives at `/home/curtis/gemini/skills/playbook-creator/`.

**Key constraint:** Stage atoms that work best are those with native gdm-* component equivalents or static HTML (no inline JS). Chart atoms use SVG not Chart.js. Interactive atoms (tabs, carousels) are display-only in `gdm-html-panel` due to CSP.

---

## OpenUI Atoms on Meet Stage — Dark Theme CSS Override Pattern (June 2026)

Added 10 OpenUI/Thesys atoms (`form`, `form_input`, `form_select`, `form_radio_group`, `form_checkbox_group`, `form_switch_group`, `form_slider`, `form_date_picker`, `modal`, `follow_up_chips`) with full `web_article.py` renderers.

**Key renderer-surface tension:** `web_article.py` is shared — renderers output light-theme colors (`#3c4043` text, `#fff` backgrounds, `#dadce0` borders) suited to the blog. The Meet stage has a dark background. Resolution: **dark-theme CSS override block in each playbook** (`_CSS` variable) rather than making renderers dual-theme. The override pattern uses attribute substring selectors: `*[style*='color:#3c4043']{color:#e2e8f0!important;}`.

**CSS override scope warning:** `*[style*='background:#fff']` is too broad — it caught the modal dialog div and made it transparent (5% white = invisible on dark). Narrowed to `label[style*='background:#fff']` (radio/checkbox item labels only). For the modal dialog itself, updated the renderer to output dark colors directly (`background:#1e293b`, `color:#f1f5f9`) since it's stage-primary.

**CSS-only modal:** `<label for="id">` → `<input type="checkbox" id="id">` → CSS sibling `#id:checked ~ .backdrop{display:flex!important;}` works correctly in standalone Chromium (Playwright-verified). Inline `display:none` on the checkbox must NOT be used — it was the previous CSS specificity bug. Hiding goes in the `<style>` block only: `#id{display:none;}`.

**Hex-alpha opacity in dark context:** `#accent0d` (5% opacity) and `#accent44` (27% opacity) are invisible on dark backgrounds. Always use `_hex_to_rgba(accent, 0.12)` / `_hex_to_rgba(accent, 0.45)` for chip backgrounds/borders to get proper `rgba()` values.

**Schema surface gates matter:** Renderer stubs and schema entries are two different registrations. Surface compatibility in `atoms/schema.yaml` drives the README compat table via `generate_compat_table.py`. If `incompatible_on` for a surface is set, it overrides `works_on` in the generator — stale incompatible entries silently hide working atoms from the table. Check and regenerate after any new renderer work.


## Sourcing from non-OSS design systems (2026-06-12)

**The inspiration-reference tier:** Not all design system sourcing requires formal license attribution. Three tiers:
1. **Derived works** (ported source code) → `THIRD-PARTY-NOTICES.md` + `source:` in schema
2. **OSS schema adaptation** (props re-expressed, e.g. OpenUI/shadcn) → attribution in notices + MANIFEST
3. **Pattern inspiration** (public documentation, no code distribution) → `vendors/<vendor>/MANIFEST.md` only, `source:` stays as `a2ui-catalogue`

Vercel Geist is tier 3 — documented at vercel.com/geist/introduction but not MIT-published. We reference it as inspiration in `vendors/vercel/MANIFEST.md`; the atoms are original a2ui-catalogue work.

**Geist gap analysis result:** 56 of 70 Geist components already had A2UI equivalents; 11 were layout primitives. Only 6 genuine gaps, of which 2 were worth implementing: `choicebox_group` and `feedback_prompt`.

**`choicebox_group` pattern:** Card-style selection uses `label:has(input:checked)` — the `:has()` pseudo-class (Chrome 105+, Firefox 121+, Safari 15.4+) lets a parent `label` react to its own hidden child `input:checked`. This is cleaner than the sibling selector trick used for stars. Render a `<style>` block with the scoped class selector (unique per-atom hash prefix) rather than inline styles, since `transition` and pseudo-class rules can't be expressed inline.

**CSS star rating (row-reverse trick):** HTML order: input5→label5→input4→label4...input1→label1. `flex-direction:row-reverse` makes label1 leftmost (star 1). `input_N:checked ~ label` selects all labels AFTER input_N in DOM — which are labels N, N-1...1, matching visual stars 1→N from the left. `label:hover ~ label, label:hover` gives hover preview of fill. No JavaScript needed.

---

## Motion-first vs content-first vendor sourcing (2026-06-13)

**The gap:** All prior vendor sources (shadcn, Flowbite, OpenUI, UIverse) are content-first — they solve layout and data display. None of them are motion-first. This is why the catalogue had zero animation atoms before Aceternity and Magic UI sourcing. The correct mental model: source from **motion-first libraries** when the need is animation, not from content libraries.

**Aceternity UI (8 atoms, ~60 total components):** MIT. Almost entirely React + Tailwind CSS. Two-thirds require JS event listeners (mousemove, scroll, canvas, WebGL) — documented in `vendors/aceternity/MANIFEST.md` as JS-dependent, not implemented. The CSS-achievable third maps cleanly to pure `@keyframes` atoms: `marquee_strip`, `typewriter_text`, `animated_border_card`, `aurora_background`, `dot_grid_background`, `shimmer_button`, `card_stack`, `meteor_shower`.

**Magic UI (4 atoms):** MIT. More animation-primitive focused than Aceternity. `blur_fade_in`, `glow_button`, `animated_beam`, `encrypted_reveal` are all pure CSS/SVG — no Framer Motion needed for the visual effect. `source_inspiration` field in schema tracks these as pattern-inspiration rather than derived works.

**`source_inspiration` field:** Added to all 12 Aceternity/Magic UI atoms. Sits alongside `source: *a2ui` to credit the visual pattern without claiming code derivation. Format: `{ name, url, note }`.

**The CSS-only constraint is a feature, not a limitation.** The renderer generates a static HTML string pushed into `gdm-html-panel`. No React runtime, no Framer Motion. Every animation atom must be expressible as `@keyframes` + CSS transitions. This rules out mousemove tracking, scroll events, canvas/WebGL — but it also means zero client-side JS dependencies and zero CSP concerns.

**`gas-sidebar` as a new surface (2026-06-13):** Google Apps Script `HtmlService` iframe — 300px max width. CSS animations work. Key degradation rules vs meet-stage: (1) `blur_fade_in` should use `direction: "none"` to avoid translateX/Y clipping at iframe edge; (2) `animated_beam` SVG is constrained to 300px, use short node labels; (3) bento-style multi-column layouts collapse to single column. Added to schema surface definitions for new motion atoms and backfilled on `glow_button`, `typewriter_text`, `animated_beam`, `blur_fade_in`.

**Parked ideas — gas-sidebar co-pilot pattern:** Three deferred ideas worth revisiting if the use case shifts to a live Sheets co-pilot (agent reacts to selected cells): (1) Context Hydration — `getA2UIContext()` Apps Script shim sends selected cell range as `initialContext` before WebSocket opens; (2) Stateless Intent Protocol — `client_intent` envelope carries surface + componentId + cell coordinates back to server on button click; (3) Cross-surface sync — bind Meet stage and Sheets sidebar sessions to same `room_id` for simultaneous broadcast. None of these are atom-level work; they're server plumbing. Parked because current playbooks are pre-authored and don't need live sheet data.

---

## Sidebar as standalone A2UI surface & web-app-as-stage pattern (2026-06-13)

**Sidebar is an A2UI surface independent of Meet.** The GAS `HtmlService` iframe runs in any Google Workspace product — Sheets, Docs, Slides, Gmail. The atom catalogue renders cleanly at 300px. This means the same playbook vocabulary that drives a Meet main-stage can power a document co-pilot sidebar, a Sheets review assistant, or a Gmail compose helper. Meet is one host, not the only host.

**Web URL as stage, sidebar as controller.** Rather than sidebar + main-stage being two halves of the same Meet add-on, the more interesting pattern is: sidebar = controller plane (browse playbook, select slide, push to stage), web URL = the stage itself (polls or subscribes for the active slide). Any participant with the URL sees the current slide in full-screen. This decouples the renderer from the Workspace surface entirely — the stage can be a TV, a second monitor, or a shared screen.

**Two-plane sidebar pattern proven.** Controller plane (top): browse/preview full deck. Participant plane (bottom): enter a space_id, poll `sidebar_current` every 3s, mirror whatever is live on stage. The pattern is working in GAS: `google.script.run` → `UrlFetchApp` server-side avoids CORS; graceful async-builder fallback (`inspect.iscoroutine` + `"__sidebar__"` space_id) prevents 500s for live-data slides.

**GAS Web App as renderer + Sheets as playbook storage.** Playbooks don't have to live in Python files on Cloud Run. A Google Sheet could store slides as rows (slide_id, builder_type, config JSON), a GAS Web App could read that sheet and render atoms as HTML, and Cloud Run becomes the AI-only layer (scoring, recommendations, live data). This would make playbooks editable by non-engineers and remove the deploy step from content changes.

**Cloud Run as AI-only layer.** The natural decomposition once Sheets-as-playbook is in place: Cloud Run handles everything that needs a model (generate slide content, score audience response, recommend next slide), GAS handles everything that is static structure (playbook definition, slide metadata, basic rendering). This is a cleaner separation than the current monolith where Cloud Run owns both the atom renderer and the AI logic.

**Painter's Algorithm requires global face sort, not per-object sort.** When two 3D objects visually interleave (a rocket core and its SRBs), sorting faces within each object separately and painting object-by-object produces cross-object see-through. All quads from all cylinders must be collected into a single array and sorted in one pass before any paint call. The per-object pattern only works safely when objects are guaranteed not to overlap in screen space.

**Isometric depth key is (wx + wz), not wz alone.** In an isometric projection where screen_y ∝ (x+z)*SIN30 - y, the true depth ordering key is x+z. Sorting on z alone gives the right order for objects arranged along the depth axis but breaks for objects displaced laterally. Averaging (wx+wz) over all four face vertices gives a stable per-face depth that correctly handles any cylinder orientation.

**Winding order is the single most important correctness invariant for Lambertian shading.** For a cylinder growing in +Y with faces built from [base_i, top_i, top_n, base_n], the cross product of edge01 × edge02 points outward. Reversing to [base_i, base_n, top_n, top_i] gives an inward normal — all dot products with the sun vector go negative, all faces clamp to ambient floor, and the solid appears invisibly dark against the background. The symptom (translucent-looking panels) looks like a depth sort bug but is actually a winding bug.

**Composite scenes require rendering-tier parity across all elements.** A high-fidelity foreground (solid Lambertian aircraft) next to a wireframe background (skeletal rocket) breaks the perceptual frame — the viewer's eye immediately resolves the mismatch as a production error. Every element in a shared viewport must be rendered at the same pipeline tier. Adding a second solid-surface pass to the background is lower effort than it looks, because the same ring/project/sort/shade infrastructure is already present and can be called with scaled coordinates.

**GAS canvas atoms achieve production 3D rendering with zero external dependencies.** Flat-shaded Painter's Algorithm with Lambertian normals, a virtual sun vector, and per-frame animation loops — running entirely through native Canvas 2D paths inside an HtmlService iframe — produces results developers assume require WebGL or a three.js dependency. The CSP sandbox constraint turns out to be a forcing function toward a simpler, faster renderer.

**Multi-atom fleet views expose a shared-projection architecture decision.** When three isometric atoms with different SC and vertical offsets share one canvas, the clean pattern is a single `proj(x,y,z)` whose `SC` and `OY` variables are set at the top of each draw function rather than being constants. This lets each aircraft own its own scale and visual center without duplicate projection code. The tab-switch resets all state variables for the incoming aircraft to their initial values, giving a fresh animation cycle every time the user switches.

**Three simultaneous livery dropdowns unlock visual cross-comparison.** Rather than a single livery selector that only applies to the active aircraft, three always-visible dropdowns let users pre-configure all three vehicles and switch instantly between them with no UI state loss. The pattern — one livery database per vehicle, three independent `lavX` variables, three change listeners — is minimal and eliminates any need for tab-aware livery routing logic.

**A shared `paintFaces(sf, pts, getC, amb)` helper removes the only duplicated code path in multi-actor canvas scenes.** The Lambertian rasterizer is identical for every polygon mesh actor (A321neo, H160, and in principle any future mesh-based atom). Extracting it as a four-argument function with a `getC(type)` material dispatcher and configurable `amb` ambient floor handles all actors cleanly without template overhead.

---

## Substrates, primitives, and the catalogue as the connective layer (2026-06-24)

**The substrate prediction playing out across three layers simultaneously.** The conviction that 2026 is about substrates and primitives — not new capabilities — is visible in the work: A2UI is the presentation substrate (typed schema vocabulary, renderer handles the rest), a2py is the operations substrate (typed JSON payload, primitive dispatch handles the rest), and skills are the knowledge substrate (typed descriptor, agent resolution handles the rest). Three different domains, one pattern.

**projects.yaml is the first cross-substrate artefact.** A machine-readable inventory that maps human context (project description, repo, URL) to a2py vocabulary (target alias, service name, Firestore collection names) means an AI can reason about infrastructure without being told what to infer. The vocabulary chain is: intent → project schema → valid target → valid primitive → valid args. Fully deterministic because each layer constrains the next.

**Skills belong in the same catalogue.** Right now skills live as flat SKILL.md files. The same typed-descriptor pattern applied to skills would make them discoverable: an agent asks "what can I do for this project?" and gets back skills whose `a2py_target` entries match the project, whose input/output contracts are declared, and whose triggers are enumerable. The catalogue becomes the connective tissue between what the AI knows (skills), what it can touch (projects), and what it can do (a2py primitives).

**FinOps as a natural audit loop.** With `projects.yaml` declaring expected resources and a2py able to describe and query them, the delta between expected state and actual GCP state becomes automatable. Cost per service via BQ billing export, idle detection via log absence, orphaned resources with no inventory entry — all of these are queries against the substrate, not bespoke scripts. The black box of cloud spend becomes a typed, queryable catalogue.

**The unifying insight: declarative intent + typed vocabulary = deterministic action, at every layer.** A2UI proves it for UI. A2py proves it for GCP operations. The skill catalogue will prove it for agent capabilities. The substrate is not the AI — it is the vocabulary the AI operates within.

---

## Billing as a substrate layer — typed FinOps primitives (2026-06-24)

**The billing moat is smaller than it looks.** GCP deliberately makes billing feel like a UI-only concern — budget alerts live in a Console workflow, notification channels require manual wiring, export configuration has no `gcloud` CLI command. But the underlying APIs are fully addressable. Every step is automatable once you know the surface: `bq mk` for dataset creation, Cloud Billing REST API for export configuration, `gcloud billing budgets create` for alert thresholds, `gcloud pubsub topics add-iam-policy-binding` for the IAM grant the Console hides. The billing moat is mostly unfamiliarity, not genuine restriction.

**The guardian pattern reduces to five typed steps.** The billing-guardian concept that previously required mixed UI/CLI setup is now a single `gcp.billing_guardian_setup` primitive: fetch project number (billing SA requires numeric ID), create Pub/Sub topic, grant billing SA publisher rights (the hidden step), create budget with Pub/Sub channel, create push subscription to guardian URL. One call, full wiring, audited. The step that previously broke the pattern — the IAM grant on a Pub/Sub topic (resource-level, not project-level) — is now `gcp.pubsub_topic_iam_add`.

**Two detection layers are better than one.** Budget threshold alerts evaluate on a ~1h cycle — not 24h (that's BigQuery billing export lag, a different system). For a 4Gi scheduler-triggered service, 1-2h detection is acceptable but not ideal. Adding `gcp.billing_poller_setup` (Cloud Scheduler → guardian → `billing_budget_describe` every 20 min) tightens detection to 20 minutes with no change to the guardian function. The two layers are complementary: passive alerts prove the billing system is wired; active polling closes the gap between evaluation cycles.

**Labels are the connective tissue between cost and inventory.** The billing export's `labels` column is the bridge. Once `a2py-target`, `a2py-owner`, `a2py-category`, and `a2py-sensitivity` are applied to every Cloud Run service, `gcp.finops_by_target` groups cost by those dimensions directly. Unattributed cost (NULL target) and no-owner cost are surfaced as separate signals. Unattributed = missing label. No-owner = labeled service with no `owner:` field in `targets.yaml`. Both are gaps that cost money and have no accountable person.

**The enforcement mechanism is financial visibility, not policy.** No one needs a mandate to label services when unattributed spend appears on a shared cost query. `(unattributed): £3.40` next to `techmusings-prod: £1.20` is its own enforcement. The label convention is a financial instrument, not a governance document.

**`targets_audit` closes the inventory loop.** Once services carry labels, `gcp.targets_audit` reads them across all projects and returns: matched (known target, label agrees), ghost (labeled a2py-managed but not in targets.yaml), unlabeled (no a2py labels — predates the system or deployed outside workflow), stale (in targets.yaml but no live service). Ghost services are the AI drift signal made explicit: they carry `owner: null` in the audit output and appear as unattributed cost in BQ. Two independent signals pointing at the same service.

**targets_sync returns suggested_labels ready to pass to cloud_run_label.** For unlabeled services that match a known target by service name, `targets_sync` derives the full label set (a2py-target, a2py-owner, a2py-category, a2py-sensitivity) from the targets.yaml entry. The output can be passed directly into a `cloud_run_label` call. Detection → suggested fix → apply — no manual label construction.

**The FinOps layer is the same pattern as everything else.** Typed schema, declared intent, deterministic primitive dispatch, audit log. `billing_export_bq_enable` is not a special billing tool — it is a payload like any other, validated against the same schema, recorded in the same audit trail. The billing substrate sits alongside the UI substrate (A2UI) and the operations substrate (a2py) because the same typed vocabulary pattern applies at every layer where AI operates and consequences accumulate.

---

## From 353 to 467 — closing the web surface gap, then shipping the pipeline (2026-06-29)

**The gap was bigger than the README said.** Coming in, the web surface showed 353 renderers against 467 schema atoms — 114 missing. Not stubs, not partial — just absent. The work today was mechanical but not trivial: four batches across a full session, each batch syntax-checked independently before appending, tests running green after every merge. The renderer file went from ~11k lines to ~22k. Every atom in the schema now has a working web renderer.

**f-string escaping in Python is a genuine footgun at this scale.** Two classes of error appear when generating HTML inside Python f-strings at volume: brace escaping (`{` must become `{{`, and a stray third `}` in `}}}` silently becomes a syntax error), and backslash-in-expression errors (Python 3.11 prohibits `\"` inside f-string expressions). The fix is consistent: precompute any conditional HTML fragment as a named variable, then compose with plain string concatenation. No f-strings with embedded backslashes, no inline ternaries with quotes. Once the pattern was established, batches were clean on first syntax check.

**The build script was pointing at the wrong renderer.** `generate_atom_pages.py` imported from `web-article/renderer.py` — a 905-line stub that predates all the work. The site would have deployed with zero previews for the 114 new atoms. The fix was one line: rewire to `renderers/web_article.py`, which is the canonical 22k-line renderer. The old stub stays for now as reference, but nothing should import from it.

**CI/CD converts the renderer from a local artifact to a deployed product.** Before today, deploying meant: remember to run the build script, remember to run wrangler, hope nothing changed between the last manual deploy and now. After today: push to main, GitHub Actions runs the build, Cloudflare gets the update. The pipeline took about 30 minutes to wire up correctly — `account_id` in wrangler.toml, wrangler-action pinned to a commit SHA (not a floating tag), `CF_API_TOKEN` scoped tightly to the single Worker. The roast panel flagged three Criticals before the first push; all three were fixed before anything went live.

**Scoping the Cloudflare token to a specific Worker is the right default.** The UI offers "entire account", "specific domain", or "specific Worker". Specific Worker is correct — if the token leaks, the blast radius is one Worker deployment, not the whole account. The permission is `Workers Scripts: Write` + `Account Settings: Read`. The token goes in GitHub Secrets, not in Cloudflare's runtime variables panel (which doesn't accept variables on a static-assets Worker anyway).

**History rewriting is a one-shot operation, not a chore.** 78 commits with a personal email in a public repo is the kind of thing that feels hard to fix but takes three minutes with `git filter-repo`. The right identity for a project repo is `a2uicatalog@users.noreply.github.com` — GitHub's noreply format, no personal email exposed, no domain required. One rewrite, force push, done. Future commits inherit the repo-local config.

**The catalogue is now a live-deployed product, not a local script.** Push to main → build → deploy. The atom vocabulary is published, versioned, and reachable. The next step is making it useful as a reference surface — not just a list of atom names, but a browsable vocabulary that agents and developers can query to understand what each atom renders and when to use it.
