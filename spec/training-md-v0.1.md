# training.md — Domain Spec v0.1

**Status:** Draft v0.1 (2026-07-02)
**Domain selector:** `training`
**Consumers:** deterministic MD→payload parser (GAS add-on) → `training` runbook → A2UI renderer
**Reference output:** the clasp KT runbook app (`clasp-runbook.json`)

This document is the complete output contract for producing a compliant
`*.training.md` file from a source document. It is designed to be handed
to an LLM (Gemini Gem, Claude, etc.) *together with* the source material.
Everything after "Model Instructions" is normative.

---

## Model Instructions

You are transforming a source document (README, tutorial, runbook, tool
documentation) into a compliant `training.md` file.

1. **Omit any section the source document does not support. Do not invent
   content to satisfy the template.** A sparse output is compliant; a
   fabricated one is not. If the source has no troubleshooting content,
   there is no `# Troubleshooting` section in your output.
2. Quote commands, paths, URLs, and identifiers **exactly** as they appear
   in the source. Never normalise, abbreviate, or "improve" them.
3. Preserve the source's terminology in Concepts. Define terms using the
   source's own explanations where they exist.
4. Keep the step sequence faithful to the source's actual workflow order.
   Do not merge, reorder, or pad steps.
5. Include a `verify:` line on every step where the source offers any way
   to confirm success (a version command, an expected URL, a file that
   should exist, expected output). Only omit `verify:` when the source
   genuinely provides no check — never invent one.
6. Output the **entire file wrapped in exactly one fenced code block**
   (open with ```markdown, close with ```). Nothing outside the fence — no
   preamble, no commentary. The fence keeps the output copy-safe in chat
   interfaces (rendered markdown collapses frontmatter lines when copied);
   the parser strips it on intake.

---

## File Structure

A compliant file is: YAML frontmatter, then body sections in the order
listed below. `# Steps` is the **only required body section** — a training
document without steps is non-compliant. All other sections are optional
and appear only when the source supports them.

```
---
<frontmatter>
---
<intro paragraph>     (optional)
# Prerequisites      (optional)
# Concepts           (optional)
# Steps              (REQUIRED)
# Checkpoints        (optional)
# Troubleshooting    (optional)
# References         (optional)
```

An optional single intro paragraph may appear between the frontmatter and
the first section heading — one to two sentences stating what the learner
will accomplish. It renders as the lead `body` block.

---

## Frontmatter

| Key           | Required | Format                                        |
|---------------|----------|-----------------------------------------------|
| `id`          | yes      | kebab-case slug, unique, e.g. `clasp-basics`  |
| `domain`      | yes      | literal `training`                            |
| `name`        | yes      | quoted display title                          |
| `source`      | yes      | provenance of the source document (title/URL/date) |
| `license`     | yes      | licence of the **source material** (e.g. `Apache-2.0`, `Public Domain`, `Proprietary — internal use only`) |
| `source_url`  | no       | canonical URL of the source document (rendered in the attribution footer) |
| `subtype`     | no       | one of `tool-kt`, `course`, `onboarding`      |
| `audience`    | no       | one line describing the intended learner      |
| `est_minutes` | no       | integer, estimated completion time            |

The parser renders an attribution footer on every app from `source`,
`source_url` and `license` — derived works stay visibly credited on
whatever surface they are shared.

`license` is how the IP tier is declared at intake: `Proprietary` content
renders privately and is never published. If the source's licence is not
stated, write `Unknown — verify before publishing`.

No other keys are permitted. **Never** include `render:`, layout, atom
lists, or any presentation metadata — presentation belongs to the runbook,
not the content file.

---

## Section Formats

Headings may carry a pandoc-style attribute block: `{#atom_hint .weight-high}`.
Hints are **defaults, not commands** — the parser validates them against
the atom schema snapshot; an unknown hint is a warning and the runbook's
default atom is used. Weights: `.weight-high`, `.weight-medium`,
`.weight-low` (default: medium).

### `# Prerequisites` `{#prerequisite_checklist}`

A flat bullet list. Each bullet is one setup requirement, phrased so a
learner can verify it themselves.

```markdown
# Prerequisites {#prerequisite_checklist}
- Node 18+ installed
- Google account with Apps Script API enabled
```

### `# Concepts` `{#key_value}`

Bullet list of `- **term** — definition`. One term per bullet. Definitions
come from the source, one to three sentences.

```markdown
# Concepts {#key_value .weight-high}
- **clasp** — CLI that syncs local files with an Apps Script project
- **scriptId** — the project identifier stored in .clasp.json
```

### `# Steps` (REQUIRED)

Two shapes, detected by the parser — never mixed in one file:

- **Flat** (short workflows): each `##` heading is a step.
- **Phased** (multi-stage workflows): each `##` heading is a *phase*
  (`## <n> · <title>`, numbered from 0 or 1), and each `###` heading
  inside it is a step. A phase heading may carry `nav="short label"` to
  override its `jump_nav` label; unnumbered phases (e.g. `## Done`) are
  excluded from `jump_nav`. A plain prose paragraph inside a phase
  renders as a `body` atom. Use phases when the source has distinct stages
  (setup vs. configuration vs. deployment). `jump_nav` is derived from
  phase headings.

A step heading is `<n>. <title> {#command_step}` with `<n>` 1-based and
sequential (within its phase, in phased shape). The heading is followed
by a key-value block, one `key: value` per line:

| Key      | Required | Meaning                                              |
|----------|----------|------------------------------------------------------|
| `cmd`    | one of `cmd`/`do` | shell command, quoted exactly               |
| `do`     | one of `cmd`/`do` | manual action when there is no command (e.g. "approve the OAuth consent screen in the browser") |
| `expect` | no       | what the learner should observe on success            |
| `note`   | no       | one caveat or context line                            |
| `verify` | no       | how to confirm the step worked (command or check)     |

Exactly one of `cmd` or `do` per step. No prose paragraphs inside steps —
anything that isn't one of these keys belongs in `note` or doesn't belong.

Two further elements may appear inside `# Steps` (in phased shape, inside
a phase; in flat shape, between steps):

- **Callout** — a blockquote line: `> <warning or context>`. Renders as a
  `callout` atom at that position. Use for warnings that apply to the
  following step(s) rather than a single step (e.g. "login with the
  dedicated deployment account — not your personal Google account").
- **Info block** — a bold label line followed by `- key :: value` bullets.
  Renders as a `key_value` atom. Use for non-command reference material a
  learner consults during the phase (deployment modes, checklists of
  console settings, what-you-will-need lists).

```markdown
# Steps

## 0 · Prerequisites
**You will need**
- Node — LTS version via nvs
- Repo access :: read access to the deployment repository

### 1. Install clasp {#command_step}
cmd: npm install -g @google/clasp
expect: version number prints
verify: clasp --version

## 1 · Authenticate
> Login with the dedicated deployment account — not your personal one.

### 1. Authenticate CLASP {#command_step}
cmd: clasp login
note: opens a browser for OAuth consent
verify: ~/.clasprc.json exists
```

### `# Checkpoints` `{#accordion_item}`

Each pair renders as a collapsed accordion — question as header, answer
revealed on tap.

`Q:`/`A:` pairs separated by blank lines. Questions test the steps and
concepts actually present in this file — never outside material.

```markdown
# Checkpoints {#accordion_item}
Q: Where does clasp store the project binding?
A: .clasp.json in the project root
```

### `# Troubleshooting` `{#accordion_item}`

Bullet list of `- symptom :: fix`. The `::` separator is mandatory.

```markdown
# Troubleshooting {#accordion_item}
- "User has not enabled the Apps Script API" :: enable it at script.google.com/home/usersettings
```

### `# References` `{#resources_list}`

Bullet list of URLs, optionally `- label — url`.

---

## What the Parser Derives (never author these)

The MD file contains **content only**. The training runbook derives all
machinery deterministically (verified against the recovered
`clasp-runbook.json` reference: 7 per-step `ValueStore` done-states, a
`done_count` Computed summing them, `progress_pct` derived from that):

- `jump_nav` — generated from phase headings (or step headings in flat shape)
- progress — one `ValueStore` per `command_step` + `Computed` done-count and percentage
- `actions`, `wire` bindings, dividers between phases — from the runbook template
- layout order, surface theming, accent palette — runbook + surface config

If you are tempted to write any of these into the MD, the content is in
the wrong layer.

---

## Lint Rules

Errors (parser rejects; message round-trips to the authoring LLM):

| Code | Rule |
|------|------|
| E01  | missing or malformed frontmatter |
| E02  | missing required frontmatter key (`id`, `domain`, `name`, `source`, `license`) |
| E03  | `domain` is not `training` |
| E04  | no `# Steps` section, or `# Steps` has zero steps |
| E05  | step missing both `cmd` and `do`, or has both |
| E06  | step numbering not sequential from 1 (within its phase, in phased shape) |
| E07  | unknown key inside a step block |
| E08  | `# Troubleshooting` or info-block entry without `::` separator |
| E09  | forbidden frontmatter key (`render`, or any presentation key) |
| E10  | `# Checkpoints` entry with `Q:` but no matching `A:` |
| E11  | flat and phased shapes mixed inside `# Steps` |
| E12  | unknown top-level section heading |

Warnings (parse succeeds; reported in coverage output):

| Code | Rule |
|------|------|
| W01  | unknown atom hint in a heading attribute (default atom used) |
| W02  | optional section absent (reported, per section, as coverage) |
| W03  | step has no `verify` (done-checkbox will be unverified self-report) |
| W04  | `license` is `Unknown — verify before publishing` |

The coverage report lists W02 findings as an audit of the **source
document**: "populated 4 of 6 sections; no Troubleshooting, no
Checkpoints" is a finding about the source's gaps, not a defect of the
output.

---

## Complete Compliant Example

The canonical round-trip fixture is `examples/clasp-deployment.training.md`
— parsed by `scripts/parse_training_md.py` it reproduces
`payloads/clasp-runbook.json` (verified in `tests/test_training_parser.py`).
The illustrative excerpt below shows the section formats.

```markdown
---
id: clasp-deployment
domain: training
subtype: tool-kt
name: "CLASP Deployment Runbook"
audience: "developers deploying Google Workspace add-ons"
source: "internal KT session + github.com/google/clasp README, July 2026"
license: "Apache-2.0"
est_minutes: 25
---

Step-by-step guide to installing CLASP and deploying Google Workspace
Apps Script projects with a dedicated deployment account.

# Concepts {#glossary .weight-high}
- **clasp** — CLI that syncs local files with an Apps Script project
- **scriptId** — the project identifier stored in .clasp.json

# Steps

## 0 · Prerequisites
**You will need**
- Node :: LTS version, managed via nvs
- Repo access :: read access to the deployment repository

### 1. Install nvs (Node Version Switcher) {#command_step}
cmd: winget install jasongin.nvs
expect: nvs command available in a new shell

### 2. Set Node version to LTS {#command_step}
cmd: nvs use lts
verify: node --version

### 3. Install CLASP globally {#command_step}
cmd: npm install -g @google/clasp
verify: clasp --version

## 1 · GCP Project Setup
> GCP setup must be done before first deploy. These are one-time steps
> per project.

**GCP Checklist**
- Apps Script API :: enabled at script.google.com/home/usersettings
- OAuth consent screen :: configured in the GCP console

## 2 · Clone & Authenticate

### 1. Pull latest code from repository {#command_step}
cmd: git pull

> Login with the dedicated deployment account — not your personal
> Google account.

### 2. Authenticate CLASP with dedicated account {#command_step}
cmd: clasp login
note: opens a browser for OAuth consent
verify: ~/.clasprc.json exists

## 3 · Push & Deploy
**Deployment modes**
- clasp push :: syncs files, updates the HEAD deployment (test)
- clasp deploy :: creates a numbered, versioned deployment

### 1. Push files to Apps Script {#command_step}
cmd: clasp push
expect: file list prints with "Pushed N files"

### 2. Create a new versioned deployment {#command_step}
cmd: clasp deploy -d "release description"
expect: deployment ID prints

# Troubleshooting {#accordion_item}
- "User has not enabled the Apps Script API" :: enable it at script.google.com/home/usersettings
- "Push failed. Files in project did not match" :: run clasp pull first, resolve, then push

# References {#link_list}
- clasp repository — https://github.com/google/clasp
```

---

## Versioning

This spec is `training-md-v0.1`. A compliant file targets exactly one spec
version; the parser declares which versions it accepts (same contract
pattern as `catalogId`/`supportedCatalogIds`). Breaking changes to section
formats or step keys bump the minor version and get a new file.
