# Express testing: data export

Static export of the evidence for the A2UI Express test programme (run 28 and 29 October 2026). Start with `index.html`: it lists every file, how it was measured, its evidence label and its caveats.

## Method

- Same six briefs throughout (T1 learning lesson, T2 metrics overview, T3 landing page, T4 filterable work-item list, T5 pricing, T6 vocabulary flashcards); the briefs are in `content-check/briefs.json`.
- Atom-choice score: set-F1 of the atoms used in a reply against answer key v2 (pinned before the comparison); key v3 differs only by also accepting `filterable_list` on T4. A reply counts as compiled if the A2UI agent SDK (0.9.0) parser accepted the whole reply. Never compare a v3 figure with a v2 figure.
- Formats: Express (SDK Express format), Direct JSON, Elemental (HTML-like). Slices of the catalogue (557 atoms) are separate catalogue files; the compiler rejects atoms outside the slice.
- Models are the measured subjects: Haiku 4.5 and 5.5, Sonnet 5.5, Opus 5.5, Gemini 3.5 Flash-Lite, 3.5 Flash and 3.8 Flash, plus the decision models Jev and Clef as choosers or routers.
- Timing is request time only wherever the set name says so; earlier Gemini runs included a rate-limit pause and are marked `first-run-timing-invalid`.
- Content check: a first reviewer graded 72 cells (rendered and payload); a second reviewer from a different model family graded the same cells from the brief, visible text and a screenshot, without model labels. Their independence is limited (each graded cells that include replies from its own model family).

## How to re-score

- Each file in `results/slice-runs/<set>/Tn.json` holds the reply (`reply`), token counts (`usage`), `secs`, validity (`valid`, `error`) and the atoms produced. Express F1 can be recomputed from the reply or the payload in `payloads/<set>/Tn.json`. For Direct JSON files the stored `produced` and `score` miss nested components: re-walk the components in the payload.
- The answer key for T1 to T6 (v2, v3) is not part of this export. The blocks tests include their briefs and answer keys in `results/blocks/inputs/`, and their scores in `results/blocks/scores/`.
- Content-check grades: `content-check/first-reviewer-grades.csv` and `second-reviewer-grades.csv`. The agreement figures in `index.html` can be recomputed from these two files.

## Licence

The measurements and tables are our own work, released under CC BY 4.0 (attribution). Model replies are the output of the named models and are included as data.

## Scrub notes

Credentials, internal paths and addresses, internal names, e-mail addresses and notes not meant for readers were removed or replaced, and the whole folder was searched for them before release (`SCRUB-REPORT.md`). Reviewers are described by role only. Old working file names are mapped to the plain names in `MANIFEST.csv`.

The `prompt_sha256` field in the raw call results (a hash of the prompt text, not a credential) has been replaced by the text "(removed for publication)" so the export carries no long hex strings.
