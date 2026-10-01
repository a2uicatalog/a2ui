# déclaration préalable — document generator

Generates the graphic attachments for a French *déclaration préalable de
travaux* (DP) for a standalone masonry boundary wall (*mur de clôture*).
Built 2026-10-01 around a real "patient zero" wall project. Reusable:
`project_schema.py`'s dataclasses are the template for any future DP project,
not just this one.

## Legal grounding (sourced, confirmed 2026-10-01)

- **Current form: CERFA n°16702\*03** — "Déclaration préalable constructions
  et travaux non soumis à permis de construire." CERFA 13703 (the number most
  web content still references) was **retired 1 Jan 2025**. Confirmed on the
  official démarche page:
  https://www.service-public.gouv.fr/particuliers/vosdroits/R2028
  (fill-in link: https://www.formulaires.service-public.gouv.fr/gf/cerfa_16702.do).
- **DP is mandatory for a mur de clôture once height ≥ 2 m** above ground, or
  **any height in a secteur protégé**. Source:
  https://www.service-public.gouv.fr/particuliers/vosdroits/F3131.
  Encoded as `dp5_elevation.DP_WALL_HEIGHT_THRESHOLD_M`.
- **The commune's PLU (Plan Local d'Urbanisme) governs** max height,
  materials, colours and placement, and overrides any generic default. A
  commonly-cited national default ceiling (absent a PLU rule) is 2.60 m
  (commune < 50 000 hab.) / 3.20 m (≥ 50 000 hab.) — **secondary; verify
  against the real commune's PLU before finalizing a real wall's design.**
  This is not automated anywhere in this directory.
- **A standalone clôture needs DP1 + DP2 + DP5 — not DP4.** DP4 (plan des
  façades et toitures) only applies when modifying an *existing* building's
  façade/roof; a new freestanding wall has no existing façade, so DP5 carries
  that role. Confirmed from an official-style municipal guide's own
  "pièces obligatoires" table ("Une clôture - DP1, DP2, DP5").
- **DP1** (plan de situation) is **out of scope here** — the official
  guidance itself says to source it directly from a public mapping site
  (géoportail.gouv.fr, cadastre.gouv.fr) or a road map, not to custom-render
  it.
- **DP2** (plan de masse, échelle 1/50–1/500): whole-plot site plan — north
  arrow, existing structures, the wall "à créer," distances to the plot
  boundary. → `dp2_plan_masse.py`.
- **DP5** (représentation de l'aspect extérieur): explicitly allowed as a
  hand sketch, a photomontage, or a computer simulation; "aucune échelle
  stricte" but proportions must be realistic; must show materials/colours
  annotated. The official example uses red leader-line callouts, e.g.
  *"Enduit lisse peint en blanc"* — reproduced exactly by
  `dp5_elevation.py`.
- DP3 (coupe) only applies if the project changes the terrain profile — not
  built here; add it if the real site's topography needs it.
- DP6/DP7/DP8/DP11 only apply in a secteur protégé — not built here.
- Each piece is submitted as its own JPEG/PNG/PDF file (not one combined
  document), so this directory outputs **one SVG + PNG per piece** — no PDF
  assembly.

**This is a drafting aid, not a legal guarantee of acceptance.** Sanity-check
every real output against the official DP5 example convention and the real
commune's PLU before submission.

## Modules

- `project_schema.py` — `WallSpec` / `PlotGeometry` / `DPProject`: the
  reusable data model. Fill in a new instance per project.
- `dp5_elevation.py` — `render_dp5_svg(project)` / `render_dp5_png(project,
  out_path)`: the dimensioned elevation + material/colour callout, i.e. the
  "front elevation" piece. Block coursing math adapted from (not imported
  from) `renderers/web_article.py`'s `_wall_calc`/`_wall_svg` — that module
  is a hobbyist cost/weight/build-time UI card with its own
  explicitly-illustrative height threshold; this module's
  `DP_WALL_HEIGHT_THRESHOLD_M` is a distinct, real, sourced legal figure.
- `dp2_plan_masse.py` — `render_dp2_svg(project)` / `render_dp2_png(project,
  out_path)`: the site plan (boundary, existing structures, wall placement,
  boundary distances, north arrow, scale bar).
- `render_wall_3d.py` — `render_wall_3d_png(project, out_path, ...)`: an
  optional photorealistic supplementary visual (NOT a substitute for DP5's 2D
  piece — DP5 itself stays `dp5_elevation.py`'s output). Reuses
  `scripts/brick_models/render_blender.py`'s Cycles camera-fit/render-settings
  infrastructure (`rb.setup_camera`, `rb.render_still`) via a plain import,
  not copy-paste; builds its own non-LDraw parametric wall slab (real metres,
  no LDU scale) with a flat rendered-masonry ("enduit") material, an outdoor
  Sun-lamp + sky-blue world (NOT a reuse of `render_blender.py`'s LEGO-scale
  Area-light rig — tuned for tens-of-cm subjects, wrong for a multi-metre
  wall), and a ground plane for scale/contact-shadow. Needs the same
  bpy-installed Python as `render_blender.py` (see
  `scripts/brick_models/requirements-blender.txt`); `intake.py`'s dossier
  generation skips it gracefully (`ImportError`) if bpy isn't installed.
- `intake.py` — the full dossier assembler. Either asks a short question set
  interactively (`collect_answers_interactively`) or reads the same shape
  from a `--answers project.json` file (scripted/reproducible), builds a
  `DPProject`, then `generate_dossier(project, out_dir, include_3d=...)` runs
  the full pipeline above into one output folder: `DP5_elevation.png`,
  `DP2_plan_masse.png`, optionally `DP5_supplementary_3d.png`,
  `project.json` (the input, for audit/reuse), and `checklist.txt` (the
  remaining manual steps — DP1 sourcing, the CERFA 16702 fill-in link, the
  PLU-verification reminder, paper-dossier count). Run with:
  `python3 declaration_prealable/intake.py` (interactive) or
  `python3 declaration_prealable/intake.py --answers data.json [--3d]`.

PNG rasterization (`dp5_elevation.py`/`dp2_plan_masse.py`) uses `cairosvg`
(same library/call convention as `scripts/a2a_agent_sketch.py`'s
`render_strokes_to_png`) — `pip install -r requirements.txt` covers it; the
SVG path works without it. `render_dp5_png_bytes`/`render_dp2_png_bytes`
return raw PNG bytes (no disk write) for a synchronous web caller; the
`_png`-suffixed functions are thin file-writing wrappers around them.

## Web intake form (`full.a2uicatalog.ai`)

Built 2026-10-01: a question-set web form backed by a small Cloud Run
service, for asking the same intake through a browser instead of a
terminal. **2D pieces only** (DP2 + DP5) — no 3D supplementary render in the
web form, that stays CLI-only (`intake.py --3d`), and runs **synchronously**
(cairosvg is sub-second, no job/poll needed).

- `declaration-prealable-api/` — a new, separate Cloud Run SERVICE (own
  `Dockerfile`/`cloudbuild.yaml`/`requirements.txt`/`server.py`, mirroring
  `premium-render-api`'s "second containerized service" shape but much
  lighter — no Job, no bucket, no signed URLs). `POST /generate` takes the
  same answers shape `intake.build_project()` consumes, returns
  `{"dp2_png_base64", "dp5_png_base64"}` directly in one JSON response.
  Access control: an `X-Render-Token` header checked via `hmac.compare_digest`
  against a Secret-Manager-bound signing key — the same established pattern
  `cloud-run-renderer/server.py` already uses, reused rather than
  reinvented, because this service's own Cloud Run URL is reachable
  independently of `full.a2uicatalog.ai`'s Cloudflare Access gate. **Needs
  `libcairo2` installed via `apt-get` in the container** — `cairosvg` binds
  the native C library via ctypes; found live that a bare `python:3.11-slim`
  image fails at request time (not import time) without it, even though a
  local dev venv with the system library already installed hides the gap.
- `build_intake_page.py` — generates `public-full/declaration-prealable/index.html`,
  gated `A2UI_CATALOG_FULL=1` (same convention as `scripts/gen_authoring.py`),
  matching `build_design_page.py`'s plain-f-string HTML style. The form posts
  to `declaration-prealable-api` and shows both images inline plus individual
  download links. `DP_API_BASE_URL` is a hardcoded literal (same convention
  as `build_design_page.py`'s `PREMIUM_RENDER_BASE_URL`) — **currently a
  placeholder** (`...-REPLACE-AFTER-DEPLOY...`), to be updated once the
  service is actually deployed. The embedded `X-Render-Token` value is read
  from Secret Manager at generation time (`DP_SIGNING_KEY` env var overrides
  for local testing) — not a secret from the page's only possible viewer, it
  exists to stop other traffic from hitting the bare Cloud Run URL.

**Verified so far**: the backend's Docker image builds and runs correctly
over real HTTP (not just the in-process Flask test client — this is where
the `libcairo2` gap was actually caught); a real headless-Chromium run
against the real generated page and the real running container filled the
form, submitted, and confirmed both images render inline with working
download links. **Not yet deployed** — no real Cloud Run service, no real
Secret Manager secret, nothing committed/pushed. See
`.claude/plans/cozy-forging-newt.md` for the full deploy plan (new
`deployments.declaration-prealable-api` + process entries in
`a2ui-private/ops/project-ops.yaml`, matching `premium-render-api-deploy`'s
shape).

## Not yet done

- Real patient-zero project data (commune, exact dimensions, plot geometry)
  — every module above has been verified with representative sample data
  and a real end-to-end `intake.py --3d` run, but not yet with the actual
  wall's own figures.
