# Corrections to our earlier post

The LinkedIn post of 2026-10-28 stays as posted; this table states what the data supports. One repeat per cell unless stated; small n. "Where" points to the section of the write-up (report/writeup.md).


| # | What the post or film said | What the data supports | Where |
|---|---|---|---|
| 1 | Film caption "Gemini Flash 1.7x" | Not valid. The Gemini adapter's 20 s pause was inside the timer, so every Gemini time was about 20 s. Re-measured on Flash-Lite with request time only: Express 2.26 s vs Direct JSON 2.94 s, about 1.3x. Gemini 3.5 Flash re-run with thinking off on 2026-10-29: median paired time ratio 1.24x (n=15, range 0.91-1.67x; Express faster in 12 of 15), about 1.7x fewer output tokens; Express compiled 15 of 18 replies, JSON 18 of 18. An earlier thinking-on run (1.19x, 0.72-3.11x, 6 of 18 JSON replies truncated at 8,192 tokens) is superseded. | writeup 3.1 |
| 2 | "Clef/Jev end to end, F1 0.79 on both" | Mixes setups. Jev-only cascade end to end: F1 0.64 at $0.0144. Clef-flash matched Jev only on the oracle-slice mean F1 (0.79). Full Clef scored 0.72 (slice C) and 0.76 (slice D) on the oracle slices, a different setup from the end-to-end 0.64. | writeup 3.3 |
| 3 | "Plain agent 0.77-0.94, higher" | Headline on key v2: 0.774, level with the Express setups (0.64-0.79). Key v3 (0.941) also accepts filterable_list on T4, an atom built 2026-09-25 to close a catalogue gap; the oracle slices C and D do not contain it, so Express could not pick it. The v3 gain is the catalogue, not a model; never compare v3 with v2. | report/writeup.md section 5, caveat 6 |
| 4 | "80x: next on my list" | Now tested in a minimal form, not confirmed in our tests. Complete screen 1.57 s (Jev 0.18 s + writer 1.39 s), inside Google's 0.8-1.7 s; 1.4-1.9x vs the same model writing the whole screen; 12-96x only for time-to-layout against whole-screen replies; pipeline F1 0.31 vs 0.67. Google's baseline for 80x is unstated. | writeup 3.6 |
| 5 | Headline speed-up | Headline model is Sonnet 5.5 (2.1x tokens, 2.0x time, 18 of 18 replies compiled (6 briefs x 3 repeats)). Haiku 4.5 compiled only 3 of 6 briefs unaided, so its 2.7x is not the headline. | writeup 3.1 |
| 6 | Pruning saving | About 13x cheaper per brief on Haiku 5.5 (2.6x at flat price); F1 gain is mostly one brief, not significant. A direction being explored, not enterprise adoption. | writeup 3.2 |

Also state: atom-choice F1 only, content check separate (see content-check/REPORT.md); one repeat; Google's own Jev numbers are an 11-prompt first look.
