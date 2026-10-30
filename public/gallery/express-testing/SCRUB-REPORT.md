# Scrub report

Search run over every file in this folder (2,500+ files; this report excluded because it names the patterns). Method: `grep -rIE` per pattern group, then each hit class read. Date: 2026-10-30.

| Pattern group | Hits | Result |
|---|---|---|
| Internal paths (`/mnt/`, `/home/`, `/tmp/`, `hdd2`) | 0 | Clean. One working path in the content-check report (H5) was reworded. |
| LAN addresses, ports, localhost | 0 | Clean. |
| Private repo and internal project names | 0 | Clean. |
| PM / board / agent names | 0 | Clean. One brief file said "written by" an internal agent name; changed to "written by us". |
| E-mail addresses | 0 | Clean. |
| The word Fable (whole-word) | 0 | Clean. (The substring appears only inside the vocabulary word "Ineffable" in the T6 flashcard briefs' model output; excluded by word boundary.) |
| Drafts / pre-publication notes / owner / handover | 133 lines | All content words inside model-written text or briefs ("Draft release notes", "assign owners", "copy drafted for sign-off", "Notification templates drafted"), plus one report row ("Model emitted two drafts"). One intended hit: `corrections/` names "the LinkedIn post of 2026-10-28", which is the public post the corrections refer to. README says "notes not meant for readers were removed". No internal draft or note remains. |
| Reviewer model names (Opus near review/audit, Gemini near second) | 6 | All are table rows or sentences about Opus 5.5 as a measured writer (e.g. "Express / Opus 5.5" in the grade tables, "the Opus 5.5 writer says so in its own T4 JSON reply"). Reviewers are described only as first reviewer and second reviewer from a different model family. |
| Provider-prefixed keys (`sk-`, `AIza`, `ghp_`, `xox*-`, `Bearer`) | 0 | Clean (whole-word match for `sk-`; "task-..." identifiers do not count). |
| Words secret / password / api key | 12 | All brief content in model output: "login form with email and password fields", "Password reset email", "secret management" (a feature blurb), "vendor webhook signing secret" (a work-item title). No credential. |
| Long base64 / hex (60+ chars, 32+ hex) | 218 | All are the `prompt_sha256` field in raw call results (SHA-256 of the prompt text). Not secrets. |

Other checks: no `http(s)` loads in any HTML (`src` or `href` to external hosts: none; the only URL inside HTML is an SVG namespace string in one rendered fragment); all 2,500+ relative links in the 23 HTML pages resolve to files inside the folder; index.html links: 24, all resolve. Model names remain only as measured subjects.
