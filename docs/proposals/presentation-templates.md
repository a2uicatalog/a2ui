# Presentation templates: an authored deck, compiled by code, checked by arithmetic

Draft 2026-10-08. A proposal, not built. Nothing here has been run yet; items marked **(verify)** are things I believe about
python-pptx, Google Slides' PowerPoint import or draw.io and must be confirmed in the spike.

## 1. The idea in one paragraph

A model writes a deck as small, semantic XML (slide roles and their content, no coordinates). Code compiles that XML into a
block tree and from there into PPTX (editable, opens in Google Slides), a web deck (the existing `playbook`), and optionally a
film. Layouts come from a small set of certified templates. Every template slot declares how much it can hold, so whether a
deck fits is arithmetic done at compile time, not something discovered by looking at a render. The only nondeterministic step is
the model writing the XML; everything after it is deterministic, offline and reproducible.

Non-goals: round-tripping edits made in PowerPoint back into XML; mapping the 650 UI atoms to PPTX; animation fidelity in
Slides; replacing the existing Slides artifact type.

## 2. Pipeline

1. **Author.** Model writes deck XML (or a person does). The catalogue's schema text for the slide atoms (slots, capacities)
   is what the model sees, so it writes to fit.
2. **Validate and repair.** Schema check, then capacity check. Errors are exact and addressed to the model
   ("slide 4, `headline`: 72 characters, this slot holds 48"). A bounded repair loop, then fail loudly.
3. **Compile.** XML to block tree to targets. Pure code, pinned dependencies, vendored fonts.
4. **Lint.** Read the generated PPTX back and check it against the template (section 7).
5. **Verify (optional, test content).** Upload to a Google account, convert to Slides, fetch a PNG per slide (section 8).

Steps 2 to 4 need no model and no network. The XML is the reviewable source: it diffs in git and a person can approve it before
the deterministic stamp produces the file. This is the same shape as the repo's existing runbook flow (approved markdown
stamped through a schema into an envelope).

Reproducibility: the same XML + template version + compiler version should give the same bytes. PPTX carries creation
timestamps and zip ordering, so the compiler normalises both; the XML hash, template version and compiler version are written
into the file's custom properties for provenance. Golden-file tests compare hashes. **(verify)** python-pptx can set these
without post-processing.

Declared as a process (`deck-build`: validate, compile, lint, optional verify) in the repo's process system, not improvised.

## 3. Deck XML (illustrative)

```xml
<deck template="studio-light" lang="en">
  <meta title="Q3 results" author="Finance" />
  <slide layout="title">
    <headline>Q3 results</headline>
    <subhead>Where we are and what changes next</subhead>
  </slide>
  <slide layout="big-stat">
    <headline>Revenue grew faster than cost</headline>
    <stat value="42%" label="year on year" />
    <notes>Say the cost figure out loud before the chart.</notes>
  </slide>
  <slide layout="bullets">
    <headline>Three changes</headline>
    <item>Pricing moves to annual by default</item>
    <item>Support hours extend to weekends</item>
    <item>The old dashboard is retired in March</item>
  </slide>
  <slide layout="diagram">
    <headline>How a request flows</headline>
    <diagram alt="A client calls the API, which reads from the database">
      <node id="c" shape="box">Client</node>
      <node id="a" shape="box">API</node>
      <node id="d" shape="store">Database</node>
      <edge from="c" to="a" label="HTTPS" />
      <edge from="a" to="d" />
    </diagram>
  </slide>
</deck>
```

Why XML here: closing tags make long nested output self-delimiting, partial output parses while streaming, and mixed content
(text with inline emphasis) is natural. The claim that XML beats JSON for this is unproven: run the small test in section 11
before committing the authoring format. The block tree underneath is the same either way.

## 4. Slide atoms (v0)

A new catalogue partition (`a2ui-slides-v1`), each atom a layout with typed slots, in the existing atom schema shape
(type, fields, surfaces, required-name rules). `surfaces` gains `pptx`, `google-slides`, `web`, `film`.

| Atom | Slots | Capacity (illustrative; measured in section 5) |
|---|---|---|
| `title` | headline, subhead | headline up to about 60 chars over 2 lines |
| `section` | headline | up to about 40 chars |
| `big-stat` | headline, stat value, stat label | value up to 7 chars; label up to 30 |
| `bullets` | headline, 2 to 5 items | item up to about 90 chars |
| `two-up` | headline, left, right (text or image) | each up to about 220 chars |
| `quote` | quote, attribution | quote up to about 180 chars |
| `timeline` | headline, 3 to 6 steps | label up to 24 chars, detail up to 70 |
| `comparison` | headline, 2 to 4 columns, up to 6 rows | cell up to 40 chars |
| `diagram` | headline, diagram | up to 12 nodes (section 6) |
| `image-full` | image, caption | `alt` required |
| `closing` | headline, contact lines | headline up to 50 chars |

Every slide can carry `notes`. A deck has a title, a language and an author.

## 5. Capacity: fit as arithmetic

Each slot declares geometry (from the template master), a font and size range, and a **capacity** derived from them: characters
per line, lines, items. How the numbers are produced:

- **Oracle.** For each slot, render the real font at the real slot size in headless Chromium and binary-search how much text
  fits; record the result in the template's metadata. No LibreOffice needed.
- **Safety margin.** PowerPoint's and Slides' text layout differ a little from Chromium's, so the stated capacity is about
  90% of the measured one.
- **Fonts.** Google Fonts only, vendored, so measurement is reproducible and Slides does not substitute. Embedded fonts are not
  supported on import **(verify)**.
- **Overflow policy, in order:** shrink the font within the slot's allowed range; split the slide (bullets and timelines only);
  otherwise return the exact error to the model. Never rely on PowerPoint's own shrink-on-overflow, which Slides does not
  honour reliably **(verify)**.
- **The same numbers go into the atom's schema text**, so the model writes to fit in the first place. This is the payload-guard
  idea (declare limits in the schema, enforce in code) applied to layout.

Later, optionally: a small grid solver that places several blocks on one slide by their declared minimum and maximum spans.

## 6. The diagram primitive

A guardrailed subset, in the spirit of the sketchpad's allowed-SVG validation: node shapes from an enum, colours from theme
tokens (never literals, which also keeps contrast checkable), edge and arrow styles from enums, groups, required text. Arbitrary
draw.io XML (mxGraph) can be imported into the subset with a report of what was dropped.

One block, three outputs: draw.io XML (the fully editable source), native PPTX shapes, and SVG. Layout is done by an engine
(the diagram tooling already supports Mermaid and D2 for this), not by the model, which places boxes badly. Edge routing is
the hard part for native shapes, because draw.io computes routes at render time; the first version places the SVG as a picture
(with alt text and the `.drawio` attached) and the native conversion follows with a fidelity test. A text alternative
("Client connects to API. API connects to Database.") is generated from the graph.

The draw.io build vendored in this repo has no PPTX export (it exports VSDX, PDF, PNG, SVG, HTML and XML), so the native path
is our own conversion. There may be a working converter already; see open questions.

## 7. Templates and how each is certified

A template is a `.pptx` master with named layouts and placeholders, plus theme tokens (palette, fonts) mirrored in the web CSS
under the same layout names, so the same deck renders consistently in both. Template data lives in files, so new ones can be
added without code.

**Certification, once per template version.** Generate worst-case fixtures from the capacity model for every layout in every
theme: slots filled to capacity, minimum content, a long unbroken word or number, accented characters. With 11 layouts, 3 themes
and 3 fixtures that is about 100 slides, a handful of small decks. Each goes through the lint, then Google Slides (section 8).
Results are recorded in the template's metadata, with reference thumbnails.

**The lint** reads the PPTX back (python-pptx) and checks: every slot's text within capacity; nothing outside the slide;
no overlaps; font size above a floor (proposed 18 pt body, 12 pt notes); required alt text present; a unique slide title; reading
order matches the visual order; language set; shapes match the template's declared geometry.

**Why this is the whole point:** because the template was proven at its capacity limits, any content inside those limits is safe
by construction, so each real deck needs only the cheap lint, in CI, in milliseconds.

Re-certify when the template, a font, a capacity number or the compiler changes, and on a schedule, because Google changes its
import over time.

## 8. Google Slides verification, and the PNGs

Google Slides is the real compatibility bar, since a PPTX has to open there. Approach, without a Google OAuth client: an Apps
Script the user deploys under their own account that (1) takes a PPTX, (2) converts it to a Slides file through Drive,
(3) requests a thumbnail for every slide, (4) returns the PNGs. It sends the test deck to the user's own Google account, which is
fine for test content; anything private is the user's call.

**Reading the PNGs.** The thumbnails are images a model can read. Claude reviews each against a checklist (text clipped or
overflowing a box, overlap, low contrast, wrong reading order, a missing or odd font, empty placeholders) and reports. That is a
second opinion alongside the deterministic lint. It is not the gate: a model's visual review can miss things, so a person signs
off when certifying a template, and the thumbnails are kept as references so a later run that differs visibly gets flagged.

Known loss on import, to confirm on a real file **(verify)**: animations and transitions, some fonts, charts that may arrive as
pictures. Plan around the safe core: shapes, text, tables, pictures, connectors.

## 9. Accessibility from day one

- Alt text required on every image and diagram; the schema marks it as the accessible name and the compiler refuses without it.
- A unique title per slide, a reading order, language set, notes available.
- Colour only from theme tokens that pass AA on their backgrounds (the contrast rules and harness from `docs/accessibility.md`
  apply to the web target as is).
- Font floor in the lint; no information carried by colour alone in the diagram primitive.
- Decorative shapes marked as such.

## 10. Phases

- **Phase 0, spike (about a week):** 4 layouts (`title`, `bullets`, `big-stat`, `diagram` as a picture), 1 template, XML to
  PPTX, the capacity oracle for those layouts, the PPTX lint, the Apps Script verifier returning PNGs. Success: a generated deck
  opens cleanly in Slides, the lint catches a deliberately overlong slide, and the same XML gives the same file twice.
- **Phase 1:** the rest of the v0 layouts, 3 themes, the certification suite, the web (`playbook`) renderer from the same tree.
- **Phase 2:** native diagram conversion with a fidelity test; optional film output; template authoring guide.

## 11. Experiments to run first

1. **XML vs JSON authoring:** 10 deck briefs through 2 or 3 models in each format; compare validity rate, repair rounds, and
   a blind visual score of the compiled deck.
2. **Capacity oracle vs reality:** does a slot's Chromium-measured capacity hold in Slides? Measure the gap to set the margin.
3. **Reproducibility:** compile the same XML twice on two machines and compare bytes.
4. **Blueprint vs free-written XML** (section 13): same briefs, compare validity, repair rounds and a blind visual score.

## 12. Open questions for Curtis

- How did the mxGraph-to-PPTX conversion work today (script, converter, or a model-written one)? If a script exists it is the
  starting point for the diagram path.
- Is the deck language its own domain contract (like the runbook one), or should it also be accepted as an A2UI input dialect?
  I would keep it a domain layer that compiles to blocks.
- Which output matters most first: PPTX to Slides, or the shareable web deck?
- Which brand templates, and are their fonts available as Google Fonts?

## 13. Blueprints: reach for a preset instead of writing from scratch

Added after discussion. A **blueprint** is a catalogue entry for a kind of brief (pitch, quarterly review, training, incident
review, launch): an ordered skeleton of slide layouts as deck XML, with optional and repeatable sections and a prompt per slot.
The flow becomes brief, then retrieval of a blueprint (the repo already matches a need to an atom semantically; the same
machinery applies), then the model fills the slots under the capacity limits and may add or drop slides within the blueprint's
rules. Gains: a quality floor, brand safety, much less variance, and the same runbook pattern the repo already uses. Cost:
rigidity. Test it in section 11 against free-written XML (add it as experiment 4).

## 14. PPTX as a surface for the existing catalogue

The slide atoms are new atoms, but the existing static catalogue could also gain a `pptx` surface, using the current
`works_on` / `degraded_on` / `incompatible_on` fields and the generated compatibility matrix.

Measured on 2026-10-08 from the 650 example payloads rendered by the JS renderer: **390 (60%) render as pure static HTML and CSS**
(no script, canvas, form control, media or animation); **257** of those also avoid features that convert poorly to native shapes
(SVG, gradients, shadows, transforms, filters). The rest are ruled out by motion (149), script (131), form controls (94), canvas
(35) and media (6); an atom can have several. This is a heuristic upper bound: "static" does not mean "makes sense on a slide"
(an audio player is static HTML), so the real set is a curated one to two hundred.

Getting from an atom to PPTX shapes goes through an intermediate **scene** of paint primitives (box, text, image, line, table,
chart) with absolute geometry, which fits because both a slide and an mxGraph diagram are fixed canvases. The scene serialises
to mxGraph XML (editable in draw.io) or to native PPTX. Three ways to produce the scene for an atom, used together:

1. **Snapshot** (picture with alt text): works for every atom, not editable. `degraded_on` pptx.
2. **Generic converter:** render the atom in headless Chromium at the slot width and walk computed boxes, backgrounds, borders,
   radii and text runs into shapes. The browser resolves flex and grid layout. Limits: gradients, shadows, SVG, transforms;
   PowerPoint reflows text slightly differently from the browser. Aimed at the easy 257. Fidelity is tested like everything
   else (section 7). **(verify)** that open-source HTML-to-PPTX converters exist and how good they are before writing our own.
3. **Per-atom recipes:** hand-written, semantic, best quality. For the slide atoms and a handful of heavily used ones.

First experiment: 10 easy atoms (`bullet_list`, `blockquote`, `stat_card`, `key_value`, `timeline`, `callout`, `table`, `steps`,
`pros_cons_list`, `before_after`) through the generic converter, compared with the browser render by geometry and by the PPTX
lint. Charts map better to native PPTX charts than to shapes, so the chart atoms get recipes, not the converter.

## 15. Findings: trying an HTML-to-PPTX converter on real atoms (2026-10-08)

Tested `dom-to-pptx` 2.1.2 (MIT, browser-only DOM walker that places shapes absolutely) on 15 static atoms rendered through the
JS renderer in the real host stylesheet in headless Chromium, inspecting each PPTX with python-pptx. Structure only: nothing
was opened in PowerPoint or Slides, so how it looks is unverified. Also read the documentation of the stricter `html2pptx` (the
pptxgenjs-based converter in the PPTX skill family) and counted how our atoms fare against its rules.

**Measured**
- **A converter instance hangs if a page is reused.** The first conversion worked and the next 8 all timed out. A fresh page per
  conversion fixed all 15. No built-in timeout, so wrap every call in one.
- **15 of 15 converted, mostly to native editable shapes.** Text intact in 12 exactly; one real loss (`table` dropped its caption,
  two words); two only looked lossy (an arrow or a row of stars split into separate runs).
- **Card chrome is rasterised.** In 7 of 15, a full-width RGBA picture (for example 1184 px wide) sits behind the text, standing
  in for the card's border, radius, accent bar or shadow. The text is editable, the card is not: it will not recolour with a
  theme, it is fixed at one resolution, and it has no alt text unless we mark it decorative.
- **Text is far too small for a slide.** Body text came out at about 6 to 10 pt. Atoms are designed at web density; the converter
  expects a 1920x1080 reference. A slide mode must render at slide scale, and the lint needs a font floor.
- **Font names pass through as CSS.** We got `Google Sans` (exists only in Google's apps), the generic `monospace` as a font name
  (not a real PPTX font) and `Arial`. A mapping table to the vendored Google Fonts is needed.
- **HTML tables become native PPTX tables**, which is good.
- Files are small (about 40 to 70 KB each).

**From the documentation (not tested here)**
- `dom-to-pptx`: build the HTML at 1920x1080; images and web fonts need CORS; SVG is rasterised unless `svgAsVector` is set;
  animation and transition utility classes exist; browser only; bundle is about 3.7 MB.
- Strict `html2pptx`: all text must be inside `p`, `h1`-`h6`, `ul` or `ol` or it silently disappears; no `br`; no gradients (they
  must be pre-rendered as PNG); no backgrounds, borders or shadows on text elements; web-safe fonts only; minimum 11 pt; content
  overflow is a blocking error; SVG and icons must be PNG.

**Our atoms against the strict converter.** Of 298 static atoms that contain text, **270 (90%)** have at least one text node
outside `p`/`h1`-`h6`/`ul`/`ol` (1,277 of 1,416 text nodes), so the strict converter would drop most of their text. It is the
right tool for HTML we author for slides, not for converting existing atoms. 28 static atoms use CSS gradients and 34 inline SVG.

**What this changes**
- The generic DOM walker is a usable starting point for the "easy 257" tier, but only behind a wrapper: a fresh browser page per
  atom, a timeout, slide-scale rendering, a font map, and a python-pptx pass that sets alt text and marks backing pictures
  decorative, sets reading order, enforces the font floor and repairs known losses (table captions).
- A slide mode for atoms should simplify their CSS (no shadows or gradients on cards) so more of the card is a native shape, not
  a picture.
- Template layouts stay hand-built from XML via python-pptx (sections 2 to 7); the converter does not replace them.

## 16. Calibration: layout maths and a measured preview (2026-10-08)

Found while building the CTA spike (`docs/proposals/spike-cta-deck/`). Two kinds of calibration, both cheap and both worth keeping.

**Layout maths, not hand positions.** Positions come from measured text, so a change in copy re-flows the slide:
- A column is stacked from measured heights (lines x size x line height, plus fixed gaps) and centred in the free area, so top and
  bottom margins match.
- A card is sized from its contents (padding, picture, gap, caption, padding) and centred on the column it sits beside. Hand-placing it
  left an empty band, which is what prompted this.
- `fit_text` searches size and box width for the largest size where the real wrap and the fallback-font wrap give the same number of
  lines and the last line is not a stub. One bug found on the way: scoring the wrap at the safety-reduced width optimised the wrong
  wrap. Score the nominal wrap; only require the fallback wrap to stay within the box.
- The lint reports margins, the card's offset from its column, orphans and overlaps.

**Calibrating the preview against a real render.** `calibrate_preview.py` takes the PPTX and a screenshot of how Slides drew it,
aligns the screenshot to the slide, and prints per shape where the ink landed against where the preview put it. First measurement
(one screenshot, the CTA slide): shapes within 1 px, text within about 4 px (0.04 in, under 1% of the slide width). The sign
differs by kind of text (the 44 pt title sits about 2 px lower in the real render, the 22 pt wordmark about 2 px higher), so no
single global constant fixes it. Use a tolerance budget of about 0.06 in for balance checks, judge relative layout with the preview,
and confirm final output against real renders. More screenshots would let per-style constants (line height by role) be fitted.

## 17. The target as a variable, and a clarifier (2026-10-08)

Suggested while looking at the CTA spike: ask "what is the target, PowerPoint or Google Slides?". The useful framing is that **the target
is a surface**, one of the `surfaces` names section 4 already proposes (`pptx`, `google-slides`, `web`, `film`), and a **target profile is data**:

| In the profile | Why it matters |
|---|---|
| fonts it can rely on | Slides has Google Fonts; a PowerPoint machine may lack them |
| a width safety margin | decides how much room a substituted font needs. Measured effect in the spike: target `google-slides` (3%) gives a clean two-line headline; `any` and `powerpoint` (12%) keep a safe three-line layout |
| features | animations and transitions, native charts versus pictures, autofit behaviour |
| accessibility checks | which checker's rules apply |
| how it is verified | Slides thumbnails through the Apps Script, or LibreOffice or a person for PowerPoint |

So the choice I had put to Curtis ("fallback or not") is not a manual setting. It follows from the target. The spike now has
`--target any|powerpoint|google-slides` (default `any`, which gives byte-identical output to the earlier build) and records the target in the
file's properties for provenance.

**The clarifier.** An agent should ask only what changes the output, and `target` does. Rules: infer it first (the user says "Google Slides",
has Drive connected, or says ".pptx to email"); otherwise ask once, with `any` as the stated default if they do not know; remember the
answer in the user's profile (the catalogue already has `get_profile` and `save_profile`) so it is never asked twice. The question itself can
be an A2UI surface: a small choice group whose value is a wired variable feeding the compile step, so the clarifier dogfoods the catalogue.
Blueprints (section 13) declare which variables they need and which of those are worth asking about (target, audience, length, brand).

**Cost to watch.** Every target multiplies the certification matrix (section 7). Keep the list short: `any`, `google-slides`, `powerpoint`,
and add others only when someone needs them.
