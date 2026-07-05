# Sample Source Documents — Parsing Candidates

Raw markdown fetched from public repos (never scraped from rendered
sites — no nav noise, license verifiable in-repo). Each is a candidate
input for the training pipeline: Gemini + `prompts/training-md-gem.md`
→ `*.training.md` → `scripts/parse_training_md.py` (or the in-app
builder) → live training app.

License is recorded at intake per the IP-tier rule: everything here is
tier 1–2 (publishable as showcases).

| File | Source repo | License | What it exercises |
|---|---|---|---|
| `cloudflare-workers-get-started.mdx` (+2 partials) | cloudflare/cloudflare-docs | CC-BY-4.0 | MDX transclusions — the anti-fabrication trap (first real run, see DEMO.md) |
| `gh-cli-quickstart.md` | github/docs | CC-BY-4.0 | Short clean quickstart; Liquid templating tags (`{% data … %}`) as noise |
| `kubectl-install-linux.md` | kubernetes/website | CC-BY-4.0 | Checksum-heavy multi-line commands — the quote-exactly rule; tabbed OS variants |
| `docker-engine-ubuntu.md` | docker/docs | Apache-2.0 | Hugo shortcodes; prerequisites + uninstall sections; apt repo setup blocks |
| `nvm-readme.md` | nvm-sh/nvm | MIT | Long README (1200 lines) — selection/omission discipline; troubleshooting-rich |
| `ollama-readme.md` | ollama/ollama | MIT | Modern tool README; model tables; REST API examples (non-procedural tail) |
| `vite-getting-started.md` | vitejs/vite | MIT | VitePress markdown; package-manager tabs; scaffolding flows |

Selection intent: each document stresses a different failure mode —
templating noise, checksum fidelity, length/omission judgement, mixed
procedural + reference content, and multi-variant commands where the
transformer must pick one path or ask rather than merge them.
