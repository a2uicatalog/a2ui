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
- **DP1** (plan de situation): the official guidance says to source it from a
  public mapping site (géoportail.gouv.fr, cadastre.gouv.fr) or a road map —
  **automated as of 2026-10-02** via real free/keyless French government
  open-data APIs (geocoding + a real IGN aerial/cadastral map screenshot),
  not a hand-drawn substitute. See "Real parcel data automation" below.
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
download links. **Live since 2026-10-02** at
`full.a2uicatalog.ai/declaration-prealable/` (Cloudflare-Access-gated),
backed by the deployed `declaration-prealable-api` Cloud Run service — see
`a2ui-private/ops/project-ops.yaml`'s `deployments.declaration-prealable-api`
and `processes.declaration-prealable-api-deploy`.

## Real parcel data automation (`parcel_lookup.py`, `dp1_situation.py`)

Built 2026-10-02: address → real parcel boundary, area, PLU zone, and a real
DP1 screenshot, via three free/keyless French government open-data APIs
(confirmed live, not assumed from documentation):

- **Geocoding** — `api-adresse.data.gouv.fr` (BAN): address → WGS84
  coordinates.
- **Real parcel geometry** — `apicarto.ign.fr/api/cadastre/parcelle` (IGN):
  returns the actual parcel polygon plus `contenance` — the **official
  cadastral surface area in m²**. Reprojected to local metres via a flat
  tangent-plane approximation (accurate at parcel scale, no projection-
  library dependency) — cross-checked live against a real parcel: computed
  shoelace area 236.4 m² vs. official 237 m² (~0.25% off). **Real edge case
  found live with a real user's actual address**: a correctly-geocoded BAN
  housenumber point (score 0.96) can still fall just outside every parcel
  polygon — confirmed by point-in-polygon testing the raw API response
  directly, not assumed (BAN places the point at the road-frontage/entrance,
  not always strictly inside the cadastral boundary; one real case measured
  only ~0.5m from the true parcel's own edge, essentially ON the boundary
  line). An exact-point query then legitimately returns zero features even
  though real parcel data exists. `fetch_parcel` falls back to a small
  bounding-box query and picks the nearest parcel by real point-to-boundary
  distance (not centroid distance, which is a looser, sometimes-misleading
  proxy for large/irregular parcels) when the exact point comes up empty.
  Feeds `PlotGeometry.boundary_points_m` directly — `dp2_plan_masse.py`
  needed **zero changes** to render the real (often irregular) shape, since it
  already accepted an arbitrary polygon, not just a rectangle.
- **Real building footprints** — `cadastre.data.gouv.fr`'s Etalab per-commune
  building bundle (apicarto's own "wfs-geoportail" module can't serve BDTOPO
  reliably — a real geometry-field gap confirmed in its own docs). Filtered
  to the buildings actually on this parcel via a plain point-in-polygon test
  (no geometry-library dependency), reprojected onto the **same shared
  origin** as the parcel boundary (not each polygon's own centroid — doing
  that independently silently puts the building in an unrelated local frame,
  a real bug found and fixed live 2026-10-02: the house was fetched but never
  actually reached `existing_structures`, in three separate places —
  `parcel_lookup.py` itself, `intake.py`'s CLI assembly, and the backend's
  `/lookup-parcel` response — all three now fixed and covered by regression
  tests). Also needed an explicit gzip-decompress fallback: this particular
  server sends gzip bytes regardless of the request's `Accept-Encoding`.
- **DP1 screenshot** — `data.geopf.fr/wms-r` (IGN WMS): a real aerial
  orthophoto with the cadastral parcel-boundary overlay composited on top,
  annotated with a north arrow, scale bar, and address caption. **Real
  server quirk found live**: the overlay layer returns as an opaque
  white-background image even with `TRANSPARENT=true` requested (confirmed:
  no alpha channel at all) — fixed by chroma-keying the white background to
  transparent in Pillow before compositing, rather than trusting the
  server's own transparency flag.
- **PLU zone** — `apicarto.ign.fr/api/gpu/zone-urba` (IGN Géoportail de
  l'Urbanisme): the real zone classification (e.g. "Zone urbaine
  Sauvegardée") plus the applicable règlement PDF's filename. **Honest
  limit**: this is a document *pointer*, not parsed rule values — actual
  height/material/colour limits live in that PDF's prose (non-standardised
  per commune), not reliably machine-extractable. `checklist.txt` surfaces
  the real document name instead of a generic "go check your PLU" line, but
  a human still opens and reads it.
- **Raw aerial photo (optional)** — `parcel_lookup.fetch_aerial_photo_bytes`:
  the plain, unannotated IGN orthophoto (no cadastral overlay, no north
  arrow/scale/caption), gated behind an "Inclure la photo aérienne brute"
  checkbox in the web form (`includeRawAerial` on `/lookup-parcel`) and only
  fetched when actually requested.

Wired into both surfaces: `intake.py`'s CLI asks "look up the real parcel
boundary?" before falling back to the manual rectangle questions;
`declaration-prealable-api`'s `POST /lookup-parcel` route and
`build_intake_page.py`'s "Rechercher la parcelle réelle" button do the same
for the web form. All three outbound APIs are free and require no API key.

## Not yet done

- Real patient-zero project data (commune, exact dimensions, plot geometry)
  — every module above has been verified with representative sample data
  and a real end-to-end `intake.py --3d` run, but not yet with the actual
  wall's own figures.
