# Reviewer instructions

Extends the base review prompt (see gemini-review.yml's own comment for how
this file is picked up -- it's the action's `custom_instructions` default
path, not something wired in the workflow itself). Copied verbatim from
maison's own .github/review-instruction-additions.md, 2026-09-06, when this
repo got gemini-review.yml for the first time -- the incident below happened
in maison, not here, but the fix is generic to the underlying review action
and applies wherever it runs.

## Severity is for defects, not for topic importance

Real incident, 2026-09-05, maison PR #124: two comments on `graphic_requests.py`
were tagged 🔴 Critical while their own prose was pure praise ("This is an
excellent example of failing loudly and securely" / "a robust
defense-in-depth measure") for code that was already correct -- each also
carried a `suggestion` diff that was either a no-op (identical to the
existing code) or a regression (loosening an SVG tag allowlist). It
reproduced identically on a re-review of the same commit. The schema's only
guidance on `severity` is the bare icon list (🔴 Critical, 🟠 High, 🟡
Medium, 🟢 Low) with no rubric for when each applies -- so a comment about
security-critical code was being tagged by the importance of its *topic*,
not by whether anything was actually wrong with it.

- The `severity` field MUST reflect an unresolved DEFECT or a concretely
  necessary improvement -- never the general importance of the topic the
  code touches. Discussing a security-critical code path is not itself a
  reason to tag 🔴 or 🟠.
- If a comment's own text is praise for code that is already correct, its
  severity MUST be 🟢 (Low), never 🔴/🟠/🟡, regardless of how important
  the underlying mechanism is.
- Only include a `suggestion` diff when it fixes a real error or is a
  concrete, beneficial change. Never suggest a no-op (a diff functionally
  identical to what's already there) or a change that weakens what's being
  praised (e.g. loosening a validated allowlist). When a comment is pure
  praise, omit `suggestion` entirely -- no suggestion beats a useless or
  harmful one.
