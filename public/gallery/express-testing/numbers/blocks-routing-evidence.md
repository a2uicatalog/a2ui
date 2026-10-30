# Blocks, catalog routing and cost: evidence summary (Sonnet 5.5 writer, Express)
All numbers were recomputed from the raw results in results/blocks/ (scores in results/blocks/scores/); an independent audit matched every number to the raw files. Small tests, one writer model (Sonnet 5.5), briefs and keys written by us, 3 repeats. Nothing here is a ranking of models or formats.

## A. What Google actually says (primary source, read 2026-10-29)
Source: https://developers.googleblog.com/fast-reliable-a2ui/ . "you can reduce latency by up to 3x, and up-to 80x using decision models like Jev" (baseline not stated; 3x = A2UI Express, 80x = decision models like Jev). "Express requires up to 3x fewer tokens to generate the same kinds of UI compared to Direct JSON." "One Jev request answers the grammar's layout questions, about 30 for a screen" (a COUNT of questions, not a speed figure). Their run: tree on screen 92-298 ms, complete screen 0.8-1.7 s, 11 prompts. So the 80x is a LATENCY claim for decision models, not a token claim; the only token claim is Express vs Direct JSON, up to 3x. Our Express vs JSON results (Sonnet 5.5: 2.1x fewer output tokens, 2.0x faster) sit inside "up to 3x". Our 24x (writer input tokens) must not be compared with their 80x: different measures.

## B. A curated agent: three levels (blocks, Sonnet 5.5, Express, 8 briefs, pinned key written first)
Level 1, curated slice only (B4: 4 atoms, 48 calls): matching briefs (robot, rocket, spaceship) 9/9 right block both formats; Express 66-113 output tokens, 1.2-2.6 s vs JSON 266-591 tokens, 2.8-5.0 s; Express compiled 24/24, JSON 21/24 (3 invented-field failures). Dashboard brief (no fitting atom): forced a brick atom 0/3 refused. Key error found after the run (house and cat accepted only motion_bricks; brick_build_3d has a house shape): pinned-key scores kept, POST-HOC re-score shown side by side and labelled (Express mean F1 B1-B7 0.57 -> 1.0, JSON 0.57 -> 0.86).
Level 2, + profile (P: 3-atom slice + one-paragraph profile telling it to refuse out-of-scope, 24 calls Express): compiled 24/24, matching briefs F1 1.0, refused real-parts table and dashboard 6/6 (instructed refusals: without the instruction it refused 0/3).
Guardrail round (G, 24 calls): clear out-of-scope 6/6 refused, prompt-injection 6/6 refused, controls 6/6 correct; borderline (toy-brick bar chart, toy-brick dashboard) built bricks 6/6 (judgement, not scored).
Level 3, full catalog (L3 pilot, 2 calls only): 122,832 input tokens per request; it also picked the right block 2/2. The other 22 L3 calls were not run.
Summary: "a one-paragraph profile and a three-atom catalog kept the agent in scope: in the guardrail round it refused 12 of 12 out-of-scope requests (6 clear + 6 prompt-injection) and in level 2 another 6 of 6 (real-parts table, dashboard): 18 of 18 in all, all instructed by the profile (G prompt is byte-identical to P); unprofiled it refused 0 of 3".

## C. Catalog routing before the writer (Sonnet router, Jev router, non-LLM routers)
Router sets: R = 16 easy briefs (we wrote them); R2 = 24 harder briefs (overlaps, two-catalog, typos, French, injection, nothing-fits). Sonnet router: R 42/42 clear replies right (48/48 incl. judgement), R2 36/36 clear, 9/9 none, 10/12 two-catalog, 11/15 judgement, 6 of 72 replies EMPTY (thinking used the 256-token cap), 1.7-1.95 s, about 1,769 input tokens. Jev router (TypeSafe jev-latest, 15 candidates: 14 catalogs + none): R 15/18 on block briefs (B4 spaceship -> none x3), 21/21 cross, R2 36/36 clear, 9/9 none, 12/12 two-catalog, judgement 12/15 (Y6 toy plane -> none x3), about 0.19 s per route, about 1,456 input tokens, no malformed. Non-LLM routers (BM25, tags, hybrid) on R2 clear: 7-8/12, tags/hybrid cannot say none; a catalog gap: tags.json tags none of the 4 brick atoms. Conclusion: a decision model does the routing as accurately as the general LLM on our hard set, about 9x faster; keyword/tag routing is not enough; an embedding router was not tested.

## D. Cost and tokens of the routed path (Sonnet 5.5 writer; prices: Sonnet 5.5 2/10 USD per MTok in/out, cache hit 0.10 (https://platform.claude.com/docs/en/about-claude/pricing, 2026-10-29); Jev 42 USD per billion tokens, sourced from the provider price page)
Writer prompt: full catalog 122,832 input tokens vs routed (router + 3-atom slice) about 5,370 (Sonnet router) / about 5,060 (Jev router): 22.9x / 24.3x fewer input tokens; summed latency 3.35 s / about 1.9 s vs 4.5 s (1.3x / 2.4x; router and agent measured as separate calls, means summed). Cost per request (uncached): full 0.246 USD; Jev-routed 0.0078 (31.6x cheaper); Sonnet-routed 0.0117 (21.1x). Cached on both sides (steady state, 100% hits): full 0.0130; Jev-routed 0.00095 (13.6x); Sonnet-routed 0.0015 (8.7x). Router step only: Jev 0.00007 vs Sonnet 0.0040 per route = 56x cheaper uncached, 8.6x cached (the 56x is COST per route, driven by per-token price, not fewer tokens). 
Cost per 1,000 requests (Sonnet 5.5 writer; mean measured tokens; cached = steady-state 100% cache hits on both sides):
| | Uncached | Cached |
|---|---|---|
| Without routing (full catalog) | 246.34 USD | 12.96 USD |
| With Jev routing | 7.79 USD | 0.95 USD |
| With Sonnet routing | 11.69 USD | 1.48 USD |
Jev route alone: 0.07 USD per 1,000 routes (70 USD per million). Sonnet route alone: 3.96 USD per 1,000 uncached, 0.61 USD cached.

Caveats: uncached/cached assumptions, cache writes cost 1.25x, 5-minute TTL; routed path never run end to end; the full-catalog agent also picked right on 2/2 briefs (the saving is prompt size and cost, not accuracy).


## Correction 2026-10-30: Jev output tokens are free
Source: typesafe.ai/blog/introducing-system-one-models-and-jev, Cost row: input "$0.042 / MTok ($42 per billion tokens)", output "FREE (too cheap to meter)". Earlier Jev rows priced output at the input rate. Recomputed (same measured tokens): Jev router 0.0000612 USD per route; router step only 65x uncached (was 56x) and 10.0x cached (was 8.6x); Jev-routed per request 0.00778 uncached (7.78 per 1,000) and 0.00094 cached (0.94 per 1,000, margin about 0.1x); versus full catalog 31.7x uncached (was 31.6x) and 13.8x cached (was 13.6x). Sonnet-router rows, token ratios, latency and accuracy unchanged. See `jev_output_free_correction_2026_10_30` in blocks-routing-numbers.json.


## Reading notes
- Atoms named in these results (block_robot, block_rocket and the brick atoms) are recent catalogue additions; their pages may not be online when you read this.
- Everything above is small-n: 8 or 16 or 24 briefs we wrote, 3 repeats, one writer model. Nothing here is a ranking of models or formats.
- Raw data: results/blocks/. Numbers: numbers/blocks-routing-numbers.json.
