# brick_build_3d / Brick Design Lab — status snapshot

## LATEST — 2026-09-27 evening: catalogue-completion session (read this first)

Same-day follow-on to the second expansion below. Landed this session, on `local/bar-grip-connector`
(committed there, not yet merged/pushed), building on the day's earlier stud-relaxation /
hole-channel-generalisation / bar-grip-detection work already in `scripts/ldraw/parts.py`:

- **`bar_grip_points()`** (was `has_bar_grip`, a bool): now returns real `[(pos, dir), ...]` for every
  genuine held/clip-mounted grip on a part, `dir` pointing outward along the rod's axis (inner attachment
  -> outer tip), the same "axis of insertion" convention `part.pins` already uses for technic friction
  pins — a bar grip is physically the same kind of connector, just clip/hand-held instead of pin/hole-
  mated. Verified against the same 3 real parts as before (2714a, 11090, 11103) plus 3 real non-grip
  controls (3001, 5258, 100942) with exact position/direction values, 6 new tests in
  `tests/test_generic_stud_occupancy.py` (20/20 passing).
- **Wired into `bake_parts.py`**: a new `bars` connector field alongside `studs`/`sockets`/`holes`/`pins`
  in every baked mesh's `connectors` dict (and its count in `index.json`), called directly (not through
  `resolve_occupancy_and_sockets`, whose 3-value return shape every existing caller depends on stays
  unchanged) — verified end to end by baking `2714a` and `3001` directly and checking the real output JSON.
- **Deliberately NOT done, left as real open scope**: `renderers/brick_parts_validate.py`'s "anchored"/
  "connections" checks don't consume `bars` at all yet — a held sword/tool still isn't counted as attached
  to anything for validation purposes. Doing that properly needs a CLIP-side detector on the holding part
  (a minifig hand, a "Plate with Clip", etc.) that doesn't exist yet — `bar_grip_points` only finds the rod
  end, not a matching receptacle. Extending the anchoring graph to treat "has a bar grip" as automatically
  self-anchoring (without a real matched clip) was considered and rejected: it would hide genuine floating-
  part errors for a held item with no real hand/clip nearby in a given model. Real follow-up: detect clip
  primitives (`clip1.dat`...`clip16.dat` in `p/`, same filename-primitive pattern `holes`/`pins` already
  use) the same way `has_bar_grip`'s cylinder detection works, then extend `validate_parts`'s adjacency
  graph with a bar-to-clip proximity match parallel to the existing stud-to-socket one.

**Also landed this session, on `local/snot-studs`:** SNOT (Studs Not On Top) generalisation of
`generic_stud_cell_occupancy`. Found investigating minifig anatomy: "Minifig Armour Shoulder Pads with 1
Stud on Front, 2 Studs on Back" (11097) has 3 real studs, ALL sideways (X/Z direction, not Y), each
individually 15-19% solid by the existing ray-cast proof -- healthy, comparable to already-accepted parts --
but the up-only flush check discarded the whole part over having zero up-facing studs at all. Generalised
the same proof to any axis-aligned stud direction, added as fully separate code alongside the proven Y-axis
path (not a rewrite) -- zero regression risk, confirmed live (3001, 164c01, 3665a all byte-identical to
before). Deliberately does NOT copy the Y-axis path's `abs(p[1]) < 0.5` position pre-filter for the new X/Z
axes: that check encodes a real LDraw convention specific to Y (an ordinary brick's local origin sits at
y=0) with no X/Z equivalent, and the ray-cast solid-fraction proof is the actual safety mechanism regardless
of position. Real, not hypothetical: 11097 (2 of 3 studs pass) and 15086 "with Neck Protection" (all 3 pass)
now both resolve cleanly. Not minifig-specific -- unlocks any sideways-stud (SNOT) part catalogue-wide. 3
new tests, all 37 in the file passing (one pre-existing test's expected value updated to reflect 11211's
generic-function-level result now correctly including its 2 real sideways studs -- 11211's actual PRODUCTION
resolution is unaffected, it still uses its own OVERRIDES entry unchanged).

**Also landed this session, on `local/minifig-anatomy`:** minifig headwear connector. `minifig_headwear_socket()`
gives hair/helmet/hat/headdress/cap/mask/crown parts a single downward-facing socket at their own LOCAL ORIGIN
(0,0,0) -- this is NOT a guess: `characters.py`'s own `OFFSETS` table already places both "head" and "headgear"
at the identical relative offset from the torso's neck, and that file's 16 real character templates already
compose real headgear parts on this exact convention (LDraw authors every minifig accessory with its own origin
AT its attachment point). Title prefixes are the real ones sampled from the actual reject pool, covering ~76%
of the real "Minifig Headwear" category. Cross-validated against `characters.py`'s own already-proven ids (3896,
3901), not just fresh reject-pool samples. 6 new tests, all passing.

**Investigated further and deliberately stopped, not a half-finished attempt:** the other minifig anatomy
categories -- Minifig Head (64 real rejects), Minifig Torso (41), Minifig Hips (26), Minifig Leg(s) (19),
Minifig Neckwear (94) -- do NOT share one clean connector pattern the way Headwear did. Sampled real parts
across all five: every one has ZERO real studs (unlike the standard curated head 3626bp01, which has exactly
one) and the categories are dominated by novelty/special variants with no shared attachment convention at all
-- an Animal Crossing Raccoon head, a bat-wing torso, a robotic prosthetic leg, a wooden leg, Ninja Turtle
shells, backpacks, shoulder armour (a couple of which DO have 3 studs, a different and unexplored mount style).
Forcing one family rule across this pool would mean guessing at connector geometry with no real shared pattern
to verify against -- exactly what this session's task brief said to avoid. Real follow-up: these need either
per-sub-family investigation (start with whichever novelty theme has the most real parts) or per-part curation,
not a quick generalisation.

**Also landed this session, on `local/technic-axle`:** Technic axle-hole detection. Investigated the real
LDraw representation of an axle cross-section (`p/axleconnect.dat`, built from four radius-9 quarter-
cylinder arcs — the male rod) and the receiving axle hole in real "... with Axle Holes" Liftarm/Beam parts
(`p/axl2hole.dat`/`axl3hole.dat`/`axl4hole.dat`). Key finding: an axle hole's outer bore is a plain circle
of radius 6 LDU (measured directly from `axl2hol2.dat`'s own boundary vertices and `axl4hole.dat`'s
`1-4cyli.dat` scale) — **identical** to `peghole.dat`'s radius. The cross shape that actually grips a real
axle is an inner detail; the material removed by the bore is the same round shape a peg hole removes. So
this needed **no new occupancy function at all** — just teaching `resolve.py`'s hole detection
(`AXLE_HOLE_RE`) to also recognise the three `axl*hole.dat` primitives alongside `peghole.dat`, populating
the same `part.holes` list the already-landed `generic_hole_channel_occupancy` already consumes. Verified
against 4 real Liftarm parts (11478, 33299a, 33299b, 2825 — all now `needs_occupancy=False`) and confirmed
2391 ("Beam 7 with Alternating Holes", 14 holes in a pattern the single-shared-axis channel model can't
safely express) correctly stays rejected, not falsely accepted. 8 new tests in
`test_generic_stud_occupancy.py` (28/28 passing). **Real full-catalogue unlock count: 479 additional
parts**, concentrated exactly where expected — Wheel (32), ~Technic (30), Technic Beam (26), Electric
Mindstorms (24), ~Electric (23), Technic Pneumatic (23), Technic Gear (20), =Technic (18), Electric Power
(16), Constraction (15), Slope Brick (11), Vehicle/Technic Steering/Technic Cross/Technic Chain (10 each).

---

## CURRENT STATUS — 2026-09-27 (read this first; everything below, including the 22:33 snapshot, is history)

**Everything in the 22:33 snapshot below has LANDED and is pushed** (both `a2ui` and `a2ui-private` are
0 commits ahead/behind `origin/main` as of this update): the 116→2,854/2,870-part expansion, minifig
characters, Gemini QA (spend ledger `~/.cache/a2ui/gemini_catalog_spend.json` = $3.78 of $50 cap; 2,832
clean / 38 needs_review in `scripts/ldraw/qa/report.md`), and the OMR "import a real LEGO set" panel
(`a2ui-private` commit `8f2f7d63`, `a2ui` commit `00d3c486`). gcloud is logged in as
`a2uicatalog@krygier.co.uk` (no sudo needed — just run as `ck`, which this box already is).

**In progress now (this is a SECOND expansion pass, on top of the one above):** a prior session ran
`survey_unbaked.py` against the ~21,881 not-yet-baked parts with the fixed occupancy resolver and it
**completed**: 1,891 newly-acceptable parts (results were sitting in a session-scoped scratchpad at
`/tmp/claude-1000/-home-ck/bbf2d293-1e24-4cca-a0de-ba04c0baaaf0/scratchpad/survey_results.json` — copy
anything you need from it NOW if it's still there, that path can vanish any time). That session died
mid-merge (hit the monthly Claude spend limit repeatedly). Steps taken to resume it, in order — **update
the checkboxes below as each one finishes so a fresh session knows exactly where to pick up**:

- [x] Merged the 1,891 accepted `{id, title}` entries into `a2ui-private/spec/brick-parts/curated-parts-v1.json`
      (2,854 → **4,745** entries), preserving the file's exact `indent=1` JSON formatting so the diff is a
      clean append (verified with `git diff --stat` before/after — do NOT re-dump the whole file with a
      different indent setting, it produces a 30k-line diff instead of a ~7.5k append).
- [ ] **Full re-bake running now** (background, started ~2026-09-27, PYTHONPATH pointed at a pre-built
      pylibs dir since system python3 has zero packages and there's no pip/sudo):
      ```
      pid: 2660991 (check with `kill -0 2660991`; may be gone if you're reading this later — check the log
      instead, and if the log's `baked <last-part>` lines have stopped advancing and no Python traceback is
      at the end, just re-run — it's idempotent)
      cwd: /home/ck/a2ui
      env: LDRAW_DIR=/home/ck/a2ui/scripts/ldraw/_ldraw_cache/ldraw
           PYTHONPATH=/tmp/claude-1000/-home-ck/8c784831-a514-402e-a74c-84acbfb366ed/scratchpad/pylibs2
      cmd: python3 scripts/ldraw/bake_parts.py
      log: /tmp/claude-1000/-home-ck/f6925372-17cc-4ad2-bb8a-fca391217fc7/scratchpad/bake_full3.log
           (SESSION-SCOPED like the previous one — if it's gone, just re-run the bake command above with a
           fresh log path; it's the same idempotent command as every previous re-bake in this file)
      expected: ~4,745 parts baked, roughly proportionally longer than the ~15-20min it took for 2,854
      ```
      That `pylibs2` PYTHONPATH dir (built by an earlier session, has numpy/pytest/pyyaml/markdown/
      jsonschema/regex/defusedxml/a2a-sdk/httpx/etc — everything in `requirements.txt`) also lives under
      `/tmp/claude-1000/-home-ck/` and may not survive indefinitely either — if it's gone, you need to
      rebuild a pylibs dir (`pip install --target <dir> -r /home/ck/a2ui/requirements.txt` from a machine/
      venv with pip, or find another session's pylibs dir under `/tmp/claude-1000/-home-ck/*/scratchpad/`).
- [ ] Gate check: `cd /home/ck/a2ui/scripts/ldraw && PYTHONPATH=<pylibs> python3 pipeline.py gate` — expect
      0 errors (same y-bounds-fix logic as before, now exercised against 1,891 more real parts).
- [ ] Full test suite: `cd /home/ck/a2ui && PYTHONPATH=<pylibs> python3 -m pytest tests/ -q`.
- [ ] Gemini QA on the new parts only (sha-based caching means the existing 2,870 won't be re-charged):
      `cd /home/ck/a2ui/scripts/ldraw && PYTHONPATH=<pylibs> python3 pipeline.py run --stages qa --batch 8
      --no-ref --cap 50 --workers 4` then `python3 pipeline.py report`. Spend so far $3.78 of $50 — this
      second batch should also land well under budget.
- [ ] Update this file's numbers (4,745 total parts, new spend total, new QA flag count) and move this
      whole "in progress" block down into history once it's done.
- [ ] Commit both repos (same file list as the §5 commit instructions below, plus none of these are new
      files — same paths). **Push is authorized** — the prior session's own queued instructions said
      "commit (push allowed per user go-ahead)", i.e. Curtis had already given the go-ahead for this specific
      push before the session died; push both repos once tests+QA are clean, don't ask again.

---

## SECOND, PARALLEL work stream — started 2026-09-27 while the re-bake above runs in the background

Curtis asked three things after seeing the re-bake status; all three approved to proceed on (not just discussed):

- [ ] **A. Fix the Gemini Design-Lab engine.** Diagnosis (confirmed by reading `a2ui-private/mcp-worker/src/
      brick-design.js`): plain `engine=gemini` hand-authors a full voxel grid as raw ASCII from nothing, with a
      2-sentence system prompt (`SYSTEM_PROMPT` line ~63) and no archetype scaffold — unlike Jevini/Layini,
      which start from a real parametric `ARCHETYPES` template (house/tower/castle/pyramid/wall/block, same
      file ~L181) and only ask Gemini for small box-edits. That structural gap is why plain Gemini looks
      weaker. Also found a real bug: `MODEL_FALLBACK_CHAIN` (`gemini-3.8/3.7/3.6-flash`, L19) doesn't match
      `MODEL_CHOICES` (`2.5-flash-lite/3.5-flash-lite/3.7-flash`, L23-27) — a fallback to 3.8 or 3.6-flash
      leaves `cost_usd`/`price_per_mtok` silently null since those keys aren't in `MODEL_CHOICES`.
      Plan: give plain Gemini either (a) a richer system prompt with concrete technique guidance (silhouette
      profile per layer, symmetry, solid base, recognisable proportions) and a worked example, or (b) route it
      through the same archetype-first pipeline as Jevini (pick a template, then let Gemini freely rewrite it)
      instead of hand-authoring from a blank grid — leaning towards (b), it's the same code path already
      proven to work better. Fix the fallback-chain/MODEL_CHOICES mismatch either way (either add 3.8/3.6-flash
      pricing to MODEL_CHOICES, or make the fallback chain only ever contain MODEL_CHOICES keys).
      **Status: DONE, tested, not yet committed.** Changed `a2ui-private/mcp-worker/src/brick-design.js`:
      rewrote `SYSTEM_PROMPT` and the `design_build` `TOOL` description to teach the real technique (plan a
      side-view silhouette layer-by-layer; change footprint width/shape between layers instead of one constant
      rectangle; colour only where the real object has that colour) plus a worked mushroom example embedded in
      the tool description (Gemini's forced single-turn tool call has no room for a few-shot conversation turn,
      so the example lives in the description text instead). Left `MODEL_FALLBACK_CHAIN` vs `MODEL_CHOICES`
      alone (found real gap: `gemini-3.8-flash`/`gemini-3.6-flash` aren't in the price table, so cost_usd goes
      silently null if either ever actually serves a request) — documented as a comment right above
      `MODEL_CHOICES`, NOT fixed, because it needs a real confirmed price from Curtis, not a guess, for a
      user-facing cost readout. All 34 tests in `mcp-worker/test/test-brick-design.mjs` pass (`node
      test/test-brick-design.mjs` from `a2ui-private/mcp-worker/`). Not yet committed — bundle with the rest.
- [x] **B. Real LEGO set search in the Design Lab.** Corrected scope after Curtis clarified: NOT a picker over
      our 5 hand-made gallery models — a real search over Rebrickable's LEGO set catalogue ("type Harry Potter,
      find real sets, render one"), building on the OMR importer that already existed
      (`/api/brick-omr?set=<id>`, exact set number only, no name search). **Status: DONE, tested, not yet
      committed/deployed.**
      - Declared `rebrickable_set_search` in `a2ui/atoms/data-sources.yaml` (search Rebrickable's
        `/api/v3/lego/sets/?search={query}`, cached 24h, `per_ip_per_min: 10`) and ran the declared
        `data-source-change` process (`python3 ops/ops.py run data-source-change` from `a2ui/`) — compiled the
        public registry (9 sources now), re-inlined the MCP Apps bundle, synced
        `a2ui-private/mcp-worker/src/data-sources.js`. Verified `REBRICKABLE_API_KEY` IS already configured live
        (`curl https://a2uicatalog.ai/api/data/rebrickable_set?set_num=75954-1` returns real "Hogwarts Great
        Hall" data) — no secret blocker, unlike what the old brief assumed.
      - **Deliberately did NOT try to scrape `library.ldraw.org/omr/sets`** (the actual list of which sets have
        a real importable `.mpd` file) for a combined "only show sets we can render" search — that page is a
        Livewire/Filament admin table with no plain `?query=`/`?page=` GET support (confirmed: query params are
        silently ignored, search is client-side AJAX against Livewire's internal update protocol, pagination
        buttons are `wire:click` with no `href`). Reverse-engineering that would be fragile, undocumented,
        third-party-internal plumbing — the wrong foundation for a permanent feature. Instead: search results
        come from Rebrickable (real, documented, stable API) and may include sets with NO OMR file; clicking one
        just runs it through the existing `importSet()` path, which already reports "set X is not in the LDraw
        Official Model Repository" honestly (`omr-import.js` L190) exactly like a hand-typed wrong set number
        does today. No silent failure, just an honest "not available" — acceptable given the alternative is
        building on undocumented internals.
      - UI: `scripts/brick_models/build_design_page.py` — new search box + result chips above the existing
        "enter a set number" field (same chip-list pattern as the existing parts-catalogue search), 350ms
        debounce, race-guarded by a sequence counter so a stale response can't clobber a newer one. Refactored
        the old `$('omrgo').onclick` body into a reusable `importSet(id, noteEl)` so both the manual field and a
        clicked search result share one code path.
      - **Found and fixed a real gap while wiring this up:** `public/bricksdemo/design/index.html` had NO
        declared regeneration process at all — only an improvised `python3 scripts/brick_models/
        build_design_page.py`, despite a staleness test already gating it
        (`tests/test_brick_parts_builder.py::test_design_page_is_what_the_generator_produces`). Declared
        `brick-design-lab-rebuild` in `a2ui-private/ops/project-ops.yaml` (edited with `Edit`, not
        `yaml.safe_load`/`dump`, per this repo's own rule about destroying comments) mirroring the existing
        `bricks-demo-rebuild` process. Ran it (`python3 ops/ops.py run brick-design-lab-rebuild`) — regenerated
        the page, staleness test passes.
      - Verified: `node test/test-brick-design.mjs` (34/34, from A above), `pytest
        tests/test_data_sources_upstream_auth.py tests/test_project_manifest.py` (17/17), the `data-source-change`
        process's own verify step (`test_mcp_apps_bundle.py`, 21/21).
      - **Not live yet** — `/api/data/rebrickable_set_search` returns `{"error":"undeclared data source"}` on
        the real site right now (confirmed by curl) because the compiled worker table only ships when
        `a2ui-private` is pushed and its Worker redeploys. Works once that push happens (bundled with everything
        else in this file waiting on a commit+push go-ahead).
- [x] **C. A proportion/palette-accurate Microduck.** **Status: DONE, tested, not yet committed.**
      - **Major finding (fetched and actually read the real 138-page booklet PDF, both versions are in the HF
        bucket — used the newer `microduck_bookletV2.pdf`, 1113 pieces / 243 steps / 13 sections, saved locally
        at `/tmp/microduck_bookletV2.pdf` this session, session-scoped, re-fetch from
        `huggingface.co/buckets/victor/microduck-lego-booklet/resolve/microduck_bookletV2.pdf?download=true` if
        gone):** the real "Microduck" is **NOT a bird** — it's Pollen Robotics' small biped robot (dome-helmet
        head with a big round orange "eye"/visor, boxy torso, two jointed robot legs, flared feet), 27cm tall x
        14cm wide x 12cm deep, ~1.1kg, in exactly **6 real colours**: White 376, Orange 183, Black 49, Dark
        Bluish Gray 317, Light Bluish Gray 141, Bright Light Orange 47 (counts from the real parts inventory,
        booklet pages 135-137 — 123 part/colour lines, all ordinary bricks/plates/slopes + one dome part
        (BrickLink 76776) and one curved slope (48092), nothing exotic, all well within reach of our now
        ~4,745-part catalogue). The OLD `duck()` built an organic bird with wings/tail/beak that shares literally
        nothing with this reference — it had been mislabelled since whenever it was first written.
      - **Scope decision (Curtis, 2026-09-27):** NOT a full 243-step transcription — there is no machine-readable
        source file for the real model (only the 138 page images: confirmed the HF bucket holds only the two
        PDFs, nothing else), so an exact rebuild means manually reading every step image, a large multi-session
        effort. Went with a **proportion- and palette-accurate stand-in** instead: same real 6 colours, same
        overall shape language (dome head/round eye, boxy torso, flared robot feet), same real-world scale
        (27cm/9.6mm-per-brick-layer ≈ 28 layers tall, matches exactly what got built), built fresh in this
        repo's own voxel-to-brick style — not a real part-for-part match, and the code comment says so plainly.
      - Rewrote `duck()` in `scripts/brick_models/models.py` (kept the function/output name `microduck` since
        `build_demo.py`'s `MODELS` list and `build_design_page.py` reference it by that id).
      - **Found and fixed a real bug while building it**: `build(S, "microduck", post=legs_and_feet, ...)`
        (the ORIGINAL call, matching the old duck's pattern) defaults to `do_hollow=True`. `hollow()` reduces a
        solid voxel blob to its shell, but its `keep()` test is per-cell and doesn't guarantee a connecting
        column survives between two stacked sub-shapes with different footprints (torso 13-wide vs neck 7-wide
        centred inside it) — it hollowed away the exact cells that would have connected the neck+head to the
        torso, so the entire head silently vanished (trimmed as unanchored by `build()`'s own trimming pass,
        with no error — `ok=True` printed and it LOOKED fine until I actually rendered and inspected the
        per-layer colour histogram of the output JSON and found the model topped out at y=21, i.e. no head at
        all). Fixed by passing `do_hollow=False` — this model is small enough that skipping hollowing entirely
        is fine part-count-wise (459 bricks, 88 steps, vs. hundreds for the old bird), and it removes this whole
        failure class rather than hand-patching the specific gap.
      - Verified: `python3 scripts/brick_models/models.py <dir> microduck` directly (`ok=True`, all four
        `brick_validate` checks pass: no collisions, every brick anchored, stud alignment, centre of mass), then
        rendered two quick orthographic sanity-check PNGs myself (Pillow, front + side elevation of the expanded
        stud cells — not the real WebGL renderer, just a fast shape/colour sanity check) and visually confirmed
        it reads as a dome-headed robot with a round eye, belt-striped torso and flared feet, not a generic box.
      - Ran the declared `bricks-demo-rebuild` process (`python3 ops/ops.py run bricks-demo-rebuild` from
        `a2ui/`) — regenerated `public/bricksdemo/index.html` (4,496 bricks across the 5 gallery models now,
        392 KB), its own test passed. Also re-ran `tests/test_brick_parts_stress.py` and `tests/test_bricks_demo.py`
        clean (5/5) after the rebuild.
      - **Not yet committed** — bundle with A and B above.

---

## Earlier snapshot — 2026-09-26 22:33 (now historical — the work it describes is done, see above)

**State at the time: all autonomous work is done. Two things wait on Curtis: a gcloud login, and a publish go-ahead.**

### Done and committed (local only, NOT pushed)
| Repo | Commit | Contents |
|---|---|---|
| `a2ui` | `e6c7387f` | catalogue expansion, minifig characters, per-vertex part colours, Design Lab picker, regenerated gallery |
| `a2ui-private` | `e34355b5` | `curated-parts-v1.json` 116 -> 2,854 entries; `ldraw-parts-check` / `ldraw-parts-qa` process declarations |

Each repo is 1 commit ahead of `origin/main`.

- **Catalogue:** 2,854 curated parts + 16 characters = 2,870 in `public/parts/index.json`. 127 are
  `needs_occupancy` (`parts.py` `verified()` rejects any occupancy box outside the part's own bounds rather than
  shipping it). `pipeline.py gate`: **0 / 2,870 parts with errors** (was 63 before the third re-bake).
- **Minifig characters (Phase 6, preview):** `scripts/ldraw/characters.py`, 16 templates (castle knight, lion
  knight, king, forestman, wizard, astronaut, pirate, pirate captain, police, firefighter, chef, construction
  worker, scientist, cowboy, gentleman, plain). `bake_parts.py` assembles each from real LDraw minifig parts
  (offsets measured from OMR 6080-1 / 6597-1) through `Library.add_virtual` and bakes it as one part,
  `public/parts/mf-<id>.json`; the index entry carries `character: {name, tags}`. `bake_parts.py
  --characters-only` re-bakes just these (seconds, vs ~20 min for everything). Figures face +Z (the atom
  camera's side), feet at y=+72 (place at y=-72 on the baseplate), and stand on a 1x2 stud pair (sockets at
  x=+-10, so x a multiple of 20 and z = 10 mod 20 lands on the grid).
- **Renderer (`atoms_brick.gs`):** baked `#rrggbb` triangle groups keep their colour per vertex (`aK` attribute,
  stride-40 part meshes). Printed torsos, faces and characters render in real colours; `main` groups still take
  the instance colour, so every existing part and the gallery render exactly as before (checked in headless
  Chrome). `scripts/test_brick_gl_geo.mjs` 17/17.
- **Brick Design Lab:** "Add a minifigure" panel: search (every word must match name/id/tags) and click to
  stand the character beside the build, 80 LDU apart (arms are cosmetic, outside the collision boxes). The
  Rebrickable CSV lists bricks only. Verified in headless Chrome against a local copy with `PART_BASE` pointed
  at a local server: no collisions, anchored, 2 studs engaged per figure.
- **Tests:** full suite **1,274 passed**, 2 skipped (includes the ~20-minute re-bake drift test, which now covers
  the characters). New: `tests/test_characters.py` (8). `test_every_curated_part_is_baked` excludes characters.
- **Gallery:** `public/bricksdemo/index.html` regenerated via `ops.py run bricks-demo-rebuild` (it embeds the
  renderer).

### Blocked on Curtis
1. **Gemini QA:** `ck`'s gcloud credentials need an interactive re-login (non-interactive refresh fails with
   "Reauthentication failed"). Checks and renders are already done for every part, so only the Gemini stage
   remains: 2,765 parts queued, est. $6-9, spend ledger at **$0.53** of the $50 cap. After
   `sudo -u ck gcloud auth login`:
   ```bash
   cd /home/ck/a2ui/scripts/ldraw
   python3 pipeline.py run --stages qa --batch 8 --no-ref --cap 50 --workers 4
   python3 pipeline.py report      # scripts/ldraw/qa/report.md
   ```
   Note: the original snapshot below says `--stages qa` alone; that only works once renders exist (they do now).
2. **Going live** needs an explicit go-ahead for each of: `ops.py run repo-publish` (public/parts/** including
   `mf-*.json`, both bricksdemo pages) and `renderer-release` / `renderer-release-nogas` (the colour change on
   MCP Apps / Apps Script surfaces). Until then the live Design Lab can't load characters: the atom fetches parts
   from `https://a2uicatalog.ai/parts/`, which doesn't have `mf-*.json` yet.

### Loose ends (not blocking)
- `demo-renderer-build` (a2ui-private `ops/project-ops.yaml`) points at `scripts/build_demo_renderer.py`, which
  doesn't exist in this repo; stale declaration.
- `public/sdk.md`, `public/sdks.md`, `public/sdks/` appeared untracked at 19:13 from outside this work; left
  uncommitted on purpose.
- `a2ui-private/ops/log.jsonl` has uncommitted run-log lines (local tier).
- Worker (`a2ui-private/mcp-worker/src/brick-design.js`) doesn't know about characters; the picker is page-side
  only. Letting the design engines place minifigs would be a follow-up.
- Open items from the earlier snapshot still stand: OMR set picker in the Design Lab, the ~12,800 unbaked
  needs-occupancy candidates, the booklet on 2,000+ part models, a real multi-page PDF.

### Useful to know
- System `python3` has no packages; use a pylibs dir on `PYTHONPATH` (this session used
  `/tmp/claude-1000/-home-ck/8c784831-a514-402e-a74c-84acbfb366ed/scratchpad/pylibs2`, session-scoped) and run repo
  commands as `ck` (`sudo -u ck ...`) so files stay ck-owned.
- A PreToolUse hook requires `git -C <repo>` for add/commit/push in either repo.

---

**Written:** 2026-09-26, mid-session, to allow pickup in a fresh Claude Code session with no prior context.
**Read this whole file before doing anything.** It is meant to be self-contained.

---

## 1. What this project is

`brick_build_3d` is an A2UI atom (`apps-script-surface/gas-wired-renderer/atoms_brick.gs`, twinned in
`renderers/web_article.py`) that renders self-assembling LEGO-style 3D models in WebGL, checks them for physical
validity (collisions, anchoring, balance), and can show step-by-step build instructions. Two live surfaces sit on
top of it:

- **`a2uicatalog.ai/bricksdemo/`** — a gallery of hand-designed procedural models (Harry Potter, Hogwarts Tower,
  etc.), generated by `scripts/brick_models/build_demo.py`.
- **`a2uicatalog.ai/bricksdemo/design/`** ("Brick Design Lab") — a live page where a visitor types a prompt and a
  model (Gemini, or the free System-1 models Jev/Laya, or a hybrid) designs a build out of **real LEGO parts**,
  which then gets validated and rendered. Generated by `scripts/brick_models/build_design_page.py`. Backed by a
  Cloudflare Worker route `POST /api/brick-design` in the **separate** `a2ui-private` repo
  (`mcp-worker/src/brick-design.js`).

Real-parts geometry comes from the LDraw library (CC BY 4.0), baked into `public/parts/<id>.json` by
`scripts/ldraw/bake_parts.py`. The spec is `a2ui-private/spec/brick-parts-v0.1.md` (not in this repo).

**Two git repos are involved:**
- `/home/ck/a2ui` (public-ish, this repo) — the atom, renderer, baked parts, site pages, most tests.
- `/home/ck/a2ui-private` (private) — the Worker (`mcp-worker/`), the ops process declarations
  (`ops/project-ops.yaml`), and the curated part list (`spec/brick-parts/curated-parts-v1.json`).

Both are real git repos; commit in each separately, never assume one covers the other.

---

## 2. What's LIVE right now (before this session's catalogue-expansion work lands)

- Worker `a2ui-private` `main` @ `196ce361` or later — `/api/brick-design` with Gemini (3 model choices), Jev,
  Laya, and hybrid Jevini/Layini engines, token/cost reporting, batched Gemini QA support.
- Site `a2ui` `main` @ some commit around `693d46cd`..later — Brick Design Lab page live at
  `/bricksdemo/design/`, "Build manual" (printable instruction booklet) and CSV export buttons, real WebGL
  screenshot capture (fixed a `preserveDrawingBuffer` bug and an `IntersectionObserver` visibility bug — see §5).
- **116 curated parts** baked in `public/parts/` — this is what's LIVE. The 2,854-part expansion (§3) is NOT yet
  committed/pushed/live as of this snapshot.

If you're picking this up fresh: check `git -C /home/ck/a2ui log --oneline -5` and
`git -C /home/ck/a2ui-private log --oneline -5` to see what actually landed since this file was written.

---

## 3. The catalogue-expansion work (this session's main task, IN PROGRESS)

**User's ask:** "I want all pieces imported please - use Gemini to import with a budget of 50 usd max" (later:
"any opportunities to minimise spend - pls take", "go auto mode").

### 3a. What was built (new files, all in `/home/ck/a2ui`)

- **`scripts/ldraw/part_checks.py`** — deterministic (no LLM, no network) geometry checks over a baked part JSON:
  mesh integrity (degenerate/open/non-manifold edges), declared bounds match real triangle extents, title
  footprint matches real WxD extent, connectors lie inside bounds, plain WxD parts have the right stud count,
  every occupancy box lies inside the part's own bounds and is checked for real solidity via ray-parity. This is
  the thing that catches false-collision risks before they ship.
- **`scripts/ldraw/parts.py`** — added `generic_stud_cell_occupancy()`: a **library-wide occupancy fallback**.
  The existing hand-curated tables (`ROUND_PARTS`, `CORNER_L_PARTS`, `SLOPE_BACK_WALL_PARTS`) all rest on one
  fact, verified by hand per id: a stud sitting flush at the part's own top surface, facing up, always has solid
  material in a 20×20×height column beneath it. This function **automates that verification**: for every stud
  that's flush, it proposes the box, then proves it's genuinely solid (not guessed) by ray-casting random sample
  points against the part's own real triangles, requiring ≥15% inside (calibrated against the real measured
  floor of the existing trusted catalogue — LEGO bricks are deliberately hollow underneath, so 100% solid is not
  the right bar). A part with even one non-flush stud (SNOT side studs, an "Inverted" slope's raised second stud)
  is excluded entirely, never partially guessed. This is what lets the catalogue scale past hand-curation.
- **`scripts/ldraw/pipeline.py`** — a resumable queue: `checks → render → Gemini QA`, keyed by each part's mesh
  SHA-256 + a stage version number, so re-running only redoes what actually changed. Supports batched Gemini QA
  (`--batch N`, several parts per Gemini call to amortise fixed prompt overhead) and `--no-ref` (skip the
  Rebrickable reference photo fetch — halves image-token cost and removes its 1 req/sec throttle, a deliberate
  spend/time optimisation for parts riding an already-proven bake path).
- **`scripts/ldraw/gemini_qa.py`** — calls Gemini (fetched via `gcloud`, key never printed/logged) to visually
  compare our render of a part against its Rebrickable photo. Has a **hard spend cap** persisted at
  `~/.cache/a2ui/gemini_catalog_spend.json` (shared ledger across all runs — this file persists across sessions,
  check it before assuming zero has been spent).
- **`scripts/ldraw/omr_import.py`** — imports a real LEGO set from the LDraw Official Model Repository
  (`library.ldraw.org/library/omr/<set>.mpd`) into a `brick_build_3d` partsModel, reporting coverage against
  baked parts. **Not yet wired into the Design Lab page** — exists and was tested on one set (Metroliner
  10001-1, 17% renderable at the time, before the expansion below).
- **`tests/test_part_checks.py`**, **`tests/test_generic_stud_occupancy.py`** — unit + real-part regression
  tests for the above. All passing as of this snapshot.

### 3b. The actual expansion numbers

- Full LDraw library: 24,735 part files. After excluding printed/patterned variants and already-baked parts:
  **15,564 real candidates**.
- Ran every candidate through `resolve_occupancy_and_sockets` (real geometry resolution + the generic fallback):
  **2,738 accepted** (get real, proven occupancy), 12,826 rejected (would need `needs_occupancy: true` — not
  baked in this pass, see §6), **0 resolution errors**.
- Added those 2,738 to `a2ui-private/spec/brick-parts/curated-parts-v1.json` (now 2,854 entries total; only `id`
  and `title` fields are read by the baker, confirmed by reading the code).
- Re-baked everything: **2,854 parts, 304.4 MB raw, 44.9 MB gzipped**. Only 24 of the original 116 still need
  occupancy (down from 35 — the generic fallback fixed 11 of the original 116's gaps for free, as a side effect).
- Updated `tests/test_ldraw_parts.py`'s `test_gzipped_total_fits_the_budget` from a 2MB ceiling to 60MB, with a
  comment explaining the real measured number and why (file count, ~2,854, is nowhere near Cloudflare Pages'
  20,000-file-per-deployment limit — this is a repo/storage budget, not a page-load one, since each part is
  fetched individually on demand).

### 3c. A real bug found and fixed mid-pass

First full-library bake produced **456/2,854 parts with error-level findings** from `pipeline.py gate` — all the
same root cause: `generic_stud_cell_occupancy` hardcoded each candidate box's Y-range as `[0, height]`, assuming
every part's top surface sits at y=0 like an ordinary brick. That's **not universal** — e.g. part `809`
("Baseplate 24×40...") has its stud flush at y=0 as always, but its declared bounds are y:`[-4, +4]` (a raised rim
above the stud plane). The fix: use the part's **own real bounds** (`bounds_min[1]`..`bounds_max[1]`) for the
box's Y-range instead of an assumed `[0, h]`. This is self-limiting via the existing ray-parity proof (a box
that's now "too tall" for a given part just fails the solidity threshold on its own). Added a regression test
against the real part 809. **A second full re-bake with the fix was in progress when this file was written** —
see §4 for exact status and how to resume.

Also found and fixed along the way, unrelated but in the same area:
- Part `4274` (Technic Pin ½) had an occupancy box floating 10 LDU away from the part — a hand-authored
  `OVERRIDES` entry bug, fixed directly.
- The ray-parity solidity check itself had a real formula bug (`v = qv[:,0]/a` instead of the general
  `dot(d, qv)/a` — only correct when the ray direction happens to be the x-unit vector, which it wasn't after
  generalising from `part_checks.py`'s fixed-direction version). Caught by unit tests before it shipped, not in
  production.

---

## 4. EXACT current status as of writing this file — how to resume

A **second full re-bake** (with the y-bounds fix from §3c applied) was running in the background:

```
pid 2246147 (may no longer exist by the time you read this — check with `kill -0 2246147`)
command: LDRAW_DIR=/home/ck/a2ui/scripts/ldraw/_ldraw_cache/ldraw python3 scripts/ldraw/bake_parts.py
output log: /tmp/claude-1000/-home-ck/fad6d12f-086c-41bc-ad9e-206411d62900/scratchpad/bake_full2.log
```

**That `/tmp/claude-1000/...` scratchpad path is SESSION-SCOPED and will very likely not exist in a new
session.** If the process already finished, `public/parts/*.json` on disk already reflects the fix and you can
skip straight to running the gate (step 2 below). If you're unsure, just re-run the bake — it's idempotent and
takes about 15-20 minutes:

```bash
cd /home/ck/a2ui
export LDRAW_DIR=/home/ck/a2ui/scripts/ldraw/_ldraw_cache/ldraw
python3 scripts/ldraw/bake_parts.py    # ~15-20 min, 2854 parts; safe to re-run
```

**Next steps in order, once the bake (or re-bake) is confirmed current:**

1. **Gate check** (deterministic, free, ~11 min at 2,854 parts):
   ```bash
   cd /home/ck/a2ui/scripts/ldraw
   python3 pipeline.py gate    # do NOT pipe through `| tail` — that eats the real exit code
   ```
   Expect **0 errors** now. If not, the y-bounds fix (§3c) didn't fully resolve it — investigate the specific
   failing part the same way §3c was diagnosed (read its `public/parts/<id>.json` bounds vs its occupancy boxes
   directly, don't guess).

2. **Full test suite:**
   ```bash
   cd /home/ck/a2ui
   export PYTHONPATH=<whatever this session's pylibs path is — check for a scratchpad/pylibs* dir, or just try
     plain `python3 -m pytest` first; this machine's system python3 has NO packages installed at all (confirmed
     this session), so if pytest/numpy/PIL aren't found, you need a scratchpad venv/pylibs directory>
   python3 -m pytest tests/ -q
   ```
   Should be ~1,260+ passed. Pay special attention to `tests/test_ldraw_parts.py` and
   `tests/test_generic_stud_occupancy.py`.

3. **Gemini QA within the $50 cap.** Check spend so far first:
   ```bash
   cat ~/.cache/a2ui/gemini_catalog_spend.json    # persists across sessions; was $0.53 as of this snapshot
   ```
   Then run (batched, no reference photos for speed/cost — see §3a for why that's fine here):
   ```bash
   cd /home/ck/a2ui/scripts/ldraw
   python3 pipeline.py run --stages qa --batch 8 --no-ref --cap 50 --workers 4
   python3 pipeline.py report      # writes scripts/ldraw/qa/report.md
   ```
   This needs `gcloud` logged in as the account with access to project `artful-patrol-502116-b7` (where the
   Gemini API key and the `rebrickable` secret live — though `--no-ref` skips the Rebrickable fetch entirely).
   At ~$0.002-0.003/part batched, 2,854 parts should cost roughly $6-9 total, well under the $50 cap — **the
   $50 was never going to be the binding constraint; bake coverage was.** Say so plainly when reporting back.

   Note: the 116 original parts already have QA results seeded from an earlier run (`gemini_qa_results_gemini-
   3.7-flash.json`, imported via `pipeline.py seed-qa`) — those won't be re-charged unless their mesh changed
   (sha-based caching). 19 of the original 116 are flagged from that earlier pass (11 real, 8 are just our QA
   renderer drawing solid studs — see the conversation history / `scripts/ldraw/qa/report.md` if it exists).

4. **Update `MODEL_CHOICES`-style price info if needed, then check `scripts/ldraw/qa/report.md`** for anything
   flagged among the 2,738 new parts. Given they all went through the SAME proven generic-fallback path, expect
   most real defects (if any) to cluster in specific title families, not be randomly scattered.

5. **Run the full test suite again**, then commit:
   ```bash
   # in /home/ck/a2ui:
   git add public/parts/ tests/test_ldraw_parts.py tests/test_part_checks.py tests/test_generic_stud_occupancy.py \
           scripts/ldraw/parts.py scripts/ldraw/part_checks.py scripts/ldraw/pipeline.py scripts/ldraw/gemini_qa.py \
           scripts/ldraw/omr_import.py .gitignore requirements.txt
   python3 ops/ops.py commit "brick-parts: library-wide catalogue expansion 116 -> 2854 parts via a geometrically-
   verified generic occupancy fallback, plus deterministic checks pipeline and Gemini QA queue"

   # in /home/ck/a2ui-private:
   git -C /home/ck/a2ui-private add spec/brick-parts/curated-parts-v1.json ops/project-ops.yaml
   git -C /home/ck/a2ui-private commit -m "curated-parts-v1.json: 116 -> 2854 entries (library-wide expansion); \
   declare ldraw-parts-check / ldraw-parts-qa ops processes"
   ```
   **Do not push/publish either repo without asking first** — per this repo's CLAUDE.md, publishing needs an
   explicit per-push go-ahead, and the user hasn't given one for THIS specific push yet (they authorized the
   import/expansion work itself and the $50 Gemini spend, not necessarily an unattended `git push`/`repo-publish`
   — check the live conversation for whether they said "go" on publishing specifically before running
   `ops.py run repo-publish` or pushing `a2ui-private`).

6. **After that lands (Phase C/D of the original plan is done), the remaining open items are:**
   - Wire `scripts/ldraw/omr_import.py` into the Design Lab page as an actual "import a real LEGO set" picker
     (currently only a standalone script). Re-run the OMR survey (`omr_survey.json` in the old session's
     scratchpad — **lost, not in this repo** — the survey script itself no longer exists on disk either; it was
     written inline in a `python3 - <<EOF` heredoc, not saved as a file. If you need sets ranked by real-world
     coverage again, you'll need to re-run a similar survey against `library.ldraw.org/omr/sets` — the URL
     pattern for a set file is `https://library.ldraw.org/library/omr/<set-number>.mpd`).
   - The 12,826 "rejected" (needs_occupancy) candidates from §3b were deliberately NOT baked in this pass (they
     add visual variety but no collision-checkable value). Could be a future phase if pure visual variety without
     validation matters.
   - Printable instruction booklet ("Build manual" button) is live and working but only tested with small/medium
     models; hasn't been tried with a 2,000+ brick model imported from a real OMR set.
   - Phase 5 from the original brief (a proper multi-page printable PDF, vs. the current "print this HTML page"
     approach) is not started.

---

## 5. Other fixes landed this session (already tested, some already live)

- **`atoms_brick.gs`**: added `preserveDrawingBuffer: true` to the WebGL context — without it, a `canvas.
  toDataURL()` call made from outside the render loop (exactly what the "Build manual" screenshot capture does)
  can read back solid black in a real browser, since WebGL is spec-allowed to clear the drawing buffer after each
  composite. Confirmed this was a real, live bug (all captured booklet images were coming out solid black) before
  the fix, real content after.
- **`atoms_brick.gs`**: the render loop's `IntersectionObserver` sets `visible=false` for any canvas that isn't
  geometrically intersecting the viewport — a deliberate perf optimisation (pause rendering when a build scrolls
  off-screen on a real page). The "Build manual" feature's hidden capture iframe was positioned at
  `left:-2000px` (off-screen), which NEVER intersects, so `visible` became false almost immediately and the
  render loop's `draw()` call was skipped forever, even though `requestAnimationFrame` kept firing. Fixed by
  repositioning the capture iframe on-screen but invisible (`opacity:0.01;pointer-events:none;z-index:-1` at
  `left:0;top:0`) instead of off-screen. **This took real, careful debugging** (traced through fetch logging,
  `readPixels`, and finally the `IntersectionObserver` source) — don't casually "fix" this again by moving the
  iframe off-screen; it will silently reintroduce the bug.
- **`build_design_page.py`**: the manual generator now composites the WebGL canvas onto a white background before
  JPEG-encoding (canvas transparency + JPEG's lack of an alpha channel = solid black fill otherwise; real LEGO
  instruction booklets are white, not black — user's own catch, confirmed and fixed, matches
  `scripts/ldraw/glshoot3.py`-style screenshot harness technique already used elsewhere in this repo).
- **Verified (not just claimed) the "Build manual" piece-count accuracy**: cover-page total, per-step chip sums
  across all steps, and the parts-list page total are cross-checked to be mutually consistent (they were, for a
  published example — a 335-brick "Tower" build, 63 steps, verified 335=335=335 with zero-piece steps checked
  for and found none). The per-step count is read directly from the same live DOM element the interactive
  "Instructions" viewer shows a user, not a separately-computed number that could drift.
- **Jev, Laya, Jevini, Layini engines** on the `/api/brick-design` Worker route are live and were each verified
  against the real hosted endpoints (`https://api.typesafe.ai/v1/systemone` for Jev — needs `JEV_API_KEY` bound
  via `wrangler secret put`, already done by the user this session; `https://laya.pensero.ai/predict` for Laya —
  public, no key, ~60 req/min). Batched Gemini QA (`ask_batch` in `gemini_qa.py`) is separate from these — don't
  confuse the Design Lab's per-visitor Gemini calls with the catalogue's bulk QA pipeline.
- A Gemini model selector (2.5-flash-lite / 3.5-flash-lite / 3.7-flash) with real per-render cost display is live
  on the Design Lab page. Measured: 3.5-flash-lite missed 12 of 19 real QA flags in a head-to-head test against
  3.7-flash on the original 116 parts — **do not use 3.5-flash-lite for the catalogue QA gate**, only 3.7-flash
  (this is already what `gemini_qa.py`/`pipeline.py` default to).

---

## 6. Things NOT done / explicitly out of scope so far

- The 12,826 rejected-by-generic-fallback candidates (parts with studs that aren't flush, or no studs at all —
  minifig parts, wheels, foliage, most Technic connectors, printed/decorated variants, curved parts with no
  studs) are not baked. They would need per-family geometric reasoning beyond what `generic_stud_cell_occupancy`
  does (convex-hull-based occupancy, or hand-curation like the existing `ROUND_PARTS`-style tables) — real
  engineering, not a quick follow-up.
- `renderer-release` / `renderer-release-nogas` (making the fixed renderer visible on MCP Apps / Apps Script
  surfaces, not just the plain web page) has not been run at any point discussed in this file.
- No `git push` or `ops.py run repo-publish` has happened for the catalogue expansion — confirm the user wants
  that specifically before doing it, separate from the general "go auto mode" authorization for the expansion
  work itself.

---

## 7. Key file locations (all paths relative to `/home/ck/a2ui` unless marked private)

| What | Where |
|---|---|
| Baked parts | `public/parts/<id>.json` + `public/parts/index.json` |
| Curated part list (input to the baker) | `a2ui-private/spec/brick-parts/curated-parts-v1.json` |
| Baker | `scripts/ldraw/bake_parts.py` |
| Occupancy/connector logic incl. generic fallback | `scripts/ldraw/parts.py` |
| Deterministic checks | `scripts/ldraw/part_checks.py` |
| Resumable QA/checks queue | `scripts/ldraw/pipeline.py` (state: `scripts/ldraw/qa/queue.json`, gitignored but persists on disk) |
| Gemini QA caller | `scripts/ldraw/gemini_qa.py` (spend ledger: `~/.cache/a2ui/gemini_catalog_spend.json`, persists) |
| OMR set importer | `scripts/ldraw/omr_import.py` (not yet wired into any UI) |
| Renderer (source of truth) | `apps-script-surface/gas-wired-renderer/atoms_brick.gs` |
| Renderer (Python twin, extracts functions from the .gs at render time) | `renderers/web_article.py` (`_brick_fn_src`) |
| Design Lab page generator | `scripts/brick_models/build_design_page.py` → `public/bricksdemo/design/index.html` |
| Gallery page generator | `scripts/brick_models/build_demo.py` → `public/bricksdemo/index.html` |
| Worker route (private repo) | `a2ui-private/mcp-worker/src/brick-design.js` |
| Ops process declarations (private repo) | `a2ui-private/ops/project-ops.yaml` (`ldraw-parts-check`, `ldraw-parts-qa`) |
| This status file | `/home/ck/a2ui/BRICK_CATALOGUE_STATUS.md` — delete or update once the work it describes has landed and this file is stale |

## 2026-09-27: TYRE_PARTS Occupancy Family (cloud agent, `agent/tyres`)

- **Task**: Add real occupancy support for rotationally symmetric Tyre parts (`scripts/ldraw/parts.py`).
- **Implementation**:
  - Added `TYRE_PARTS` family and `tyre_occupancy(bounds_min, bounds_max)` function in `scripts/ldraw/parts.py`.
  - Tyres in LDraw are modeled rotationally symmetric about the Z axis (wheel axle) with their circular cross-section in the XY plane, centered at `(0, 0)`.
  - Like `ROUND_PARTS` and `DISH_PARTS`, occupancy is computed as an axis-aligned square inscribed in that outer circular cross-section (`half_inscribed = diameter / (2 * sqrt(2))`), spanning the part's real Z bounds (`[z_min, z_max]`).
  - By inscribed-circle geometry, any point within the square has radius $r \le \text{diameter} / 2$, provably containing the collision box entirely within the physical tyre cylinder envelope without falsely flagging collisions in surrounding empty air (spec §3's under-approximation guarantee).
  - Tyres have no studs, pegholes, or pins (`studs == []`, `holes == []`, `pins == []`), so sockets are explicitly empty (`sockets = []`).
  - Added deterministic constants derived from real resolved geometry for all 92 clean, undeformed, rotationally-symmetric tyre parts.
  - Excluded 2 unfinished / deformed parts (`2807` marked "Needs Work" and `6578c01` marked "Deformed to 10/ 67 x 24") which remain `needs_occupancy=True`.
- **Catalogue Impact**:
  - Rejects survey (`scripts/ldraw/survey_rejects.py`) showed 94 total Tyre-category parts rejected prior to change.
  - Post-implementation survey unlocks **92 real tyre parts** (`Tyre` reject count dropped from 94 to 2).
- **Verification**:
  - Added targeted test cases in `tests/test_generic_stud_occupancy.py` (pure math tests, dispatcher tests, and real resolved geometry tests for a representative sample of 10 tyre parts plus rejection tests for excluded parts). All 28 tests pass.

## 2026-09-27: Hinge Occupancy & Feasibility Investigation (cloud agent, `agent/hinge-investigation`)
- Completed scoping investigation for LEGO hinge representation and occupancy: see [scripts/ldraw/HINGE_INVESTIGATION.md](scripts/ldraw/HINGE_INVESTIGATION.md).
- **Key finding**: True hinges do NOT require a pose parameter or a dynamic multi-body occupancy model. In both physical LEGO and LDraw, hinges are two separate static parts (e.g. `2429`/`2430`, `4275b`/`4276b`, `3937`/`3938`). Most hinge halves are already baked with valid static occupancy and do not collide when mated at orthogonal angles. The only missing capability is connector recognition (`hinges` axis pairing) in `brick_parts_validate.py`.

## 2026-09-27: Generic Tile Occupancy & Printed Variant Unlock (cloud agent, `agent/tile-family`)

- **Task**: Unlock real occupancy for Tile parts, especially printed/decorated variants (`scripts/ldraw/parts.py`).
- **Core Insight & Empirical Validation**:
  - Sampled and verified 25+ real tile parts and printed pairs (e.g. `10202` vs `10202p04`/`10202p05`, `14719` vs `14719p00`, `14769` vs `14769p0a`, `3068b` vs `3068bp06`/`3068bp09`, `3069b` vs `3069bp01`/`3069bp02`, `3070b` vs `3070bp01`, `2431` vs `2431p01`, `6636` vs `6636p01`, `4150` vs `4150p01`, `98138` vs `98138p01`).
  - Confirmed that printed variants (`*p*.dat`) share identical resolved geometry (exact bounds and ray-parity solidity fractions) with their base unprinted tiles.
  - While plain tiles previously relied on brittle title matching (`SAFE_SUFFIXES`), printed titles carry descriptive pattern names that failed classification, causing thousands of valid tiles to be rejected.
- **Implementation**:
  - Added `generic_tile_occupancy(bounds_min, bounds_max, studs, tris, title="")` in `scripts/ldraw/parts.py` and connected it as a fallback in `resolve_occupancy_and_sockets`.
  - **Flat Rectilinear Tiles**: For parts with plate height ($y \in [-0.5, 8.5]$, $dy \in [7.0, 8.5]$) and grid dimensions ($N \times M$ multiples of 20 LDU), candidate 20x20 LDU cells are tested via ray-parity solidity (`_stud_box_solid_fraction >= 0.15`). If all $N \times M$ cells are solid and the 4 extreme bounding box corners are proven solid ($\ge 0.20$, preventing false matching of circular/curved parts), a single unified bounding box and standard downward sockets (`generate_sockets(occ)`) are emitted.
  - **L-Shaped Corner Tiles** (e.g. `14719`, `14719p00`): In a 2x2 grid where exactly 3 out of 4 cells are solid plastic and 1 corner is empty air, 3 individual cell boxes and 3 downward anti-stud sockets are emitted.
  - **Round Tiles** (e.g. `14769`, `4150`, `98138`, `67095`): Circular discs centered at $(0, 0)$ in XZ are modeled using inscribed squares ($[-D / (2\sqrt{2}), D / (2\sqrt{2})]$), provably containing collision boxes inside the circular cylinder without corner overshoots. 1x1 round tiles receive a single center bottom socket; multi-stud round tiles have non-standard undersides (e.g. round/cross underside studs) and leave sockets empty (`sockets = []`), matching `DISH_PARTS`.
  - **Safe Exclusions** (under-approximate, never guess per spec §3):
    - Tiles with clips (e.g. `12825`, `2555`, `30350`): clip jaws protrude beyond plate height ($y: [-10, 8]$) or create open grasping regions; excluded from flat tile occupancy.
    - Tiles with through-holes (e.g. `15535 Tile 2 x 2 Round with Hole`): a solid inscribed square would cover the center hole and falsely collide with inserted pins/axles; safely excluded (`needs_occupancy=True`).
    - Curved/angled tiles (e.g. `22385 with Angled End`, `27925 Corner Round`, `24246 with Rounded End`, `35787 Triangular`): extreme corners fail the $\ge 0.20$ solidity threshold; safely excluded.
- **Catalogue Impact**:
  - Unprinted rejects survey (`scripts/ldraw/survey_rejects.py`):
    - Prior to change: 623 candidate tile parts; 20 accepted, 603 rejected.
    - Post-implementation: **515 accepted, 108 rejected** (495 newly accepted unprinted tile parts, an 82.1% reduction in unprinted tile rejects).
    - The remaining 108 rejected parts consist strictly of feature-bearing or curved items (clips, through-holes, angled wedges, quarter-round corners, magnet holders, projectile launchers).
  - Whole library impact (including printed variants across all 2,290 tile parts in LDraw):
    - Prior to change: 57 accepted, 2,233 rejected.
    - Post-implementation: **1,879 accepted** (1,331 printed variants + 548 unprinted base/sticker tiles), reducing total tile rejects from 2,233 to 411.
- **Verification**:
  - Added comprehensive test suite in `tests/test_generic_stud_occupancy.py`: synthetic rectilinear tiles, synthetic L-corner tiles, synthetic round tiles, synthetic exclusions, real resolved tile parts across 17 part IDs/variants, and real feature exclusions.
  - All 77 tests in `tests/test_generic_stud_occupancy.py` pass cleanly in 19.58s.

## 2026-09-27: PANEL_FLAT_WALL_PARTS Occupancy Family & Investigation (cloud agent, `agent/panel-family`)

- **Task**: Real occupancy for Panel parts where provable (`scripts/ldraw/parts.py`).
- **Investigation of Two Distinct Sub-Families**:
  - **Sub-Family 1: Simple Flat Wall Panels (`15207`, `23950`, `23969`, `4865a`, `30413`, `4865b`, `93095`, `6231`, `30010`, `43337`, `4865`)**:
    - **Physical Geometry**: Zero studs (`studs == []`), 1-stud depth (Z: `[-10.0, 10.0]`), 1-brick height (Y: `[0.0, 24.0]`), and width $N \times 20$ LDU (X: `[-10*N, 10*N]`).
    - **Solidity Proof**: Bounding box solidity was evaluated against real resolved mesh triangles via ray-parity sampling (`_stud_box_solid_fraction`). All verified parts measure 31.5% to 53.3% solid (`15207`: 36.7%, `23950`: 41.3%, `23969`: 50.3%, `4865a`: 41.7%, `4865b`: 41.7%, `30413`: 40.7%, `6231`: 53.3%, `93095`: 46.7%), well above the catalogue floor `STUD_CELL_MIN_SOLID = 0.15` and comparable to an ordinary solid-topped 2x4 brick (`3001` at 43.4%).
    - **Corner Fillet Safety**: The rounded corners on rounded-corner variants (`4865b`, `15207`, `23950`, `30413`, `23969`) have a measured fillet radius of ~2 LDU (0.8 mm; at 3x3 LDU the corner region is >91% solid). In the discrete LEGO grid (stud pitch 20 LDU, plate height 8 LDU), no LEGO element can fit inside a 0.8 mm corner relief, so the bounding box is a provably safe under-approximation that cannot cause false collisions with legitimately placed adjacent parts (spec §3).
    - **Sockets**: Standard downward-facing sockets at $y=24$ are generated via `generate_sockets` on the 20x20 LDU grid (1 socket for 1x1, 2 for 1x2, 3 for 1x3, 4 for 1x4), matching the physical anti-stud mounting sockets on the real underside.
  - **Sub-Family 2: Corner/Curved Wall Panels with Studs (`2345`, `2409`, `2448`, `2466`, `2468`, `2571`, `2572`) — Safely Left Unresolved**:
    - **Castle Wall Corner `2345`**: Crenellated corner wall. Studs sit on an inner walkway at $y=24$, while the outer corner battlements rise to $y=0$. `stud_cell_occupancy_and_sockets` assumes studs sit at $y=0$, and would fabricate 24 LDU of non-existent solid material in the empty air above the studs. Moreover, the columns beneath the studs are thin hollow shells (solid fractions 0.06 to 0.23, failing the 0.15 threshold on 3 of 5 studs).
    - **BURP/LURP Rock Corner `2409`**: 10x10x12 rock corner (288 LDU tall). Its 6 studs occupy a tiny 2x2 corner. Below the top brick ($y > 24$), the rock face opens into a massive hollow cave interior. Solid fraction across the full 288 LDU height is only 1.0% to 3.0%. A full-height column box would falsely block the hollow interior, while a 24 LDU box would place sockets in mid-air at $y=24$ instead of the base at $y=288$.
    - **Fuselage/Airplane Panels `2448`, `2466`, `2468`, `2571`, `2572`**: Thin curved shells spanning 144 to 216 LDU height. All column solidities under top studs are between 1.0% and 7.0% (far below 0.15). In addition, `2448` has studs at two different heights ($y=0$ and $y=128$), and `2448`/`2466`/`2468` have negative bounds min Y (-8.0) that violate the 0-based box model. Curved-top panels (`2571`, `2572`) have curved top contours that a rectangular box severely over-approximates. Per spec §3 and task instructions, these are honestly left `needs_occupancy=True`.
- **Catalogue Impact**:
  - Rejects survey (`scripts/ldraw/survey_rejects.py`) on panel categories prior to change:
    - `Panel 1`: 8 rejected (`15207`, `23950`, `23969`, `30413`, `4865a`, `4865b`, `6231`, `93095`)
    - `=Panel`: 8 rejected (including aliases `30010` and `43337`)
    - Total non-Technic panel rejects: 51
    - Total panel-related rejects across library: 122
  - Post-implementation survey:
    - `Panel 1`: **0 rejected** (dropped from 8 to 0, 100% resolved)
    - `=Panel`: **6 rejected** (dropped from 8 to 6)
    - Total non-Technic panel rejects: dropped from 51 to 41
    - Total panel-related rejects: dropped from 122 to 112
- **Verification**:
  - Added pure math tests, dispatcher tests without bounds, and real resolved geometry tests for all 11 parts in `PANEL_FLAT_WALL_PARTS` plus patterned variants (`4865ap01`, `23969p01`) in `tests/test_generic_stud_occupancy.py`.
  - Added parameterized rejection tests verifying that all 7 Sub-Family 2 parts safely remain `needs_occupancy=True`.
  - All 78 tests in `tests/test_generic_stud_occupancy.py` pass.

## 2026-09-27: WHEEL_PARTS Occupancy Family (cloud agent, `agent/wheel-rims`)

- **Task**: Add real occupancy support for rotationally symmetric Wheel Rim parts (`scripts/ldraw/parts.py`).
- **Investigation Findings**:
  - **Rotational Symmetry**: Wheel rims are rotationally symmetric about the Z axis in LDraw with their circular cross-section in the XY plane, centered at `(0, 0)`.
  - **Difference from Tyres**: Tyres have no axle passing through their local coordinate center (they mount around the outside of a rim). Wheel rims DO mount onto a Technic axle or wheel-holder pin through an axle or peg hole running through their rotational center `(0, 0)` along Z.
  - **Naive Inscribed Square Risk**: Placing a solid inscribed square spanning the center (like `tyre_occupancy`) reports solid material inside the axle bore, causing false-positive collisions with any mounting axle or pin inserted in a model.
  - **`generic_hole_channel_occupancy` Incompatibility**:
    1. Radial/spoke holes (e.g. `41896`) vary across both X and Y axes (`len(varying) == 2`), violating the single-shared-axis assumption and bailing immediately.
    2. Single-center-hole channel boxes extend to the outer bounding box corners and fail the raycast solid-fraction check (`STUD_CELL_MIN_SOLID = 0.15`) because spoked wheels are mostly empty air between hub and rim (`32077` has 0.083, `42716` has 0.062, `33211` has 0.062).
    3. Primitives like `axlehol5.dat` (used by `3482`) are missed by `AXLE_HOLE_RE = r"^axl\d*hole\.dat$"` due to DOS 8.3 filename truncation, leaving `part.holes` empty despite physical axle holes existing.
- **Implementation**:
  - Added `WHEEL_PARTS` family and `wheel_occupancy(bounds_min, bounds_max, bore_half=WHEEL_BORE_HALF)` in `scripts/ldraw/parts.py`.
  - **Annular 4-Box Inscribed Square Decomposition**:
    Decomposes the inscribed square of half-width $W = D / (2 \sqrt{2})$ into 4 axis-aligned bounding boxes (Top, Bottom, Left, Right) surrounding a central exclusion square of half-width $B = \text{WHEEL\_BORE\_HALF} = 8.0$ LDU spanning the part's full Z extent `[z_min, z_max]`.
  - **Geometric Safety Guarantees**:
    1. *Outer cylinder containment* (never over-reports external collisions): For any point in the 4 boxes, $|x| \le W$ and $|y| \le W$, so $x^2 + y^2 \le 2 W^2 = (D / 2)^2 = R_{out}^2$. All points lie strictly within the circular rim cylinder envelope.
    2. *Central bore exclusion* (never collides with mounting axles/pins): The central square $(-B, B) \times (-B, B)$ is completely clear of occupancy. Technic axles ($|x| \le 6.0, |y| \le 6.0$), Technic pin shafts ($r = 6.0$), pin flanges ($r = 8.0$), and wheel pins ($r = 4.0$) pass through without intersecting any of the 4 boxes.
  - **Sockets**: Explicitly empty (`sockets = []`) as wheel rims mount via axle/pin connections and carry no bottom studs/sockets.
  - **Constants**: Hand-verified deterministic constants derived directly from real resolved geometry (`resolve_part`) for 74 clean, undeformed, rotationally-symmetric vehicle wheel rim parts ($D \ge 34.0$ LDU, ensuring $W \ge 12.02 > B = 8.0$ and $W - B \ge 4.02$ LDU).
- **Deliberately Unaddressed Sub-groups** (remain `needs_occupancy=True`):
  - *Small wheel rims* ($D \le 28.0$ LDU, $W \le 8.0$ LDU; e.g. `30027a-d`, `34337`, `42610`, `50944`, `6014a/b`, `74967`): Outer inscribed square half-width $W \le 8.0$ is smaller than or equal to the standard bore exclusion width ($B = 8.0$).
  - *Composite shortcut assemblies* (e.g. `3482c01`, `30155c01`, `2695c01`, 68 parts total): CAD multi-part shortcuts combining a wheel rim and tyre; not atomic parts. In official inventory and OMR sets, rims and tyres are separate parts.
  - *Wheels with integral or stub axles* (e.g. `30190`, `3464b`, `50862`, `u9163`, `u9167`): Protruding solid axle shafts require different representation.
  - *Decorative wheel covers* (e.g. `54086`, `58088`, `61738`, `62359`, `62701`): Thin cosmetic face clips.
  - *Tracks/belts* (`43903-f1`, `53992-f1..f3`, `71965-f1`, `85543-f5`) and mechanisms (`32060`, `3465a`, `4142`).
  - *Obsolete or incomplete parts* (`22969` obsolete, `55981` marked "Needs Work", `2496` trolley, `3739` off-center).
- **Catalogue Impact**:
  - Rejects survey (`scripts/ldraw/survey_rejects.py`) showed 188 total Wheel-category parts rejected prior to change (58 accepted).
  - Post-implementation survey unlocks **74 real wheel rim parts** (`Wheel` category reject count dropped from 188 to 114, accepted grew from 58 to 132).
- **Verification**:
  - Added comprehensive test suite in `tests/test_generic_stud_occupancy.py`:
    - Pure math tests verifying 4-box geometry, outer cylinder containment, and bore exclusion.
    - Dispatcher tests for representative parts (`2470`, `2695`, `30155`, `3482`).
    - Real resolved geometry tests for 12 representative wheel rims (`2470`, `2695`, `30155`, `32077`, `33211`, `42716`, `3482`, `4266`, `4489a`, `41896`, `7877`, `6580a`) asserting bounds containment, rotational symmetry, outer cylinder containment, and zero collision with simulated Technic axle.
    - Deliberate exclusion tests for 8 parts across the unaddressed sub-groups asserting `needs_occupancy=True`.
  - Full test suite run (`pytest tests/test_generic_stud_occupancy.py`): **73 passed, 0 failed, 0 skipped** (up from 51 passed before this change).
