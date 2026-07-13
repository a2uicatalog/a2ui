#!/usr/bin/env python3
"""
Regenerate public/catalogue/atoms-embeddings.json — a 384-dim embedding vector
per published atom (via Cloudflare Workers AI's @cf/baai/bge-small-en-v1.5),
used by mcp-worker's /api/compose to route a natural-language request to
relevant atoms WITHOUT a chat-completion call (cosine similarity in JS instead).

Why this exists: measured live (2026-07-13) that the chat-based routing call
ate ~95% of the neuron cost of a full /api/compose request (~31 of ~33-41
neurons), because it stuffs the full 468-atom vocabulary into the prompt just
to pick 1-3 relevant types. An embedding-based router does the same job for a
fraction of the cost (~0.1 neurons per request to embed the incoming prompt;
the 468 atom vectors are precomputed once, here, not per-request) while
understanding semantic similarity a plain keyword match would miss.

NOT wired into CI (unlike gen_atom_json_schemas.py) — Workers AI's env.AI
binding only exists inside a deployed Worker's runtime, and GitHub Actions
can't call it directly. This script instead talks to Workers AI through a
throwaway local `wrangler dev` Worker with an [ai] binding, which requires an
authenticated wrangler session on the account (same one used to deploy).

Run manually whenever atoms/schema.yaml's published atom set changes
meaningfully (a new atom, a renamed one, a materially reworded
compact_description) — not on every commit:

  1. python3 scripts/gen_public_catalog.py     # refresh spec.json first if schema.yaml changed
  2. mkdir /tmp/embed-gen && cd /tmp/embed-gen
     cat > wrangler.toml <<'EOF'
     name = "atom-embed-gen-scratch"
     main = "worker.js"
     compatibility_date = "2024-09-23"
     account_id = "<see mcp-worker/wrangler.toml or blog-worker/wrangler.toml>"
     [ai]
     binding = "AI"
     EOF
     cat > worker.js <<'EOF'
     export default { async fetch(request, env) {
       const body = await request.json();
       const result = await env.AI.run(body.model, body.opts);
       return Response.json(result);
     }};
     EOF
     npx wrangler dev --port 8798 &
  3. python3 scripts/gen_atom_embeddings.py --endpoint http://localhost:8798/

Commit the resulting public/catalogue/atoms-embeddings.json like any other
generated artifact.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib import request as urlreq

ROOT = Path(__file__).parent.parent
SPEC = ROOT / "public" / "spec.json"
OUTPUT = ROOT / "public" / "catalogue" / "atoms-embeddings.json"
MODEL = "@cf/baai/bge-small-en-v1.5"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", required=True,
                         help="throwaway wrangler-dev Worker URL exposing env.AI.run(model, opts) as {model, opts} -> AI response")
    args = parser.parse_args()

    spec = json.loads(SPEC.read_text())
    atoms = spec["atoms"]
    texts = [f"{a['type']}: {a.get('compact_description', '')}" for a in atoms]

    body = json.dumps({"model": MODEL, "opts": {"text": texts}}).encode()
    req = urlreq.Request(args.endpoint, data=body, headers={"Content-Type": "application/json"})
    with urlreq.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    if "error" in result:
        print(f"embedding call failed: {result['error']}", file=sys.stderr)
        sys.exit(1)

    vectors = result["data"]
    if len(vectors) != len(atoms):
        print(f"mismatch: {len(atoms)} atoms but {len(vectors)} vectors returned", file=sys.stderr)
        sys.exit(1)

    out = {
        "model": MODEL,
        "dim": result["shape"][1],
        "atoms": [
            {"type": a["type"], "vector": [round(x, 5) for x in vec]}
            for a, vec in zip(atoms, vectors)
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(out, separators=(",", ":")))
    print(f"✓ {len(out['atoms'])} atom embeddings → {OUTPUT}")


if __name__ == "__main__":
    main()
