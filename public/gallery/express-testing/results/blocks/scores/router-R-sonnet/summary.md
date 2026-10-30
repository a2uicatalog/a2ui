Condition R (catalogue router, step 1 only). Accuracy per brief and per group; JUDGEMENT cells (B7, X8) are reported separately and are NOT in any group row. No blended number.

## sonnet-5-5

| group | briefs | correct | (n replies) |
|---|---|---|---|
| block briefs, clear key (B1-B6 -> bricks) | B1,B2,B3,B4,B5,B6 | 18/18 | 18 |
| other-catalogue briefs, clear key (B8, X1-X6) | B8,X1,X2,X3,X4,X5,X6 | 21/21 | 21 |
| null brief (X7) | X7 | 3/3 | 3 |

False positives (non-block briefs, i.e. B8 and X1-X8, sent to bricks): 0/27. Misses (B1-B6 not sent to bricks): 0/18. Invalid ids: 0. Malformed: 0.

| brief | group | accept | correct | routed (count over repeats) |
|---|---|---|---|---|
| B1 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B2 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B3 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B4 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B5 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B6 | block | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B7 | judgement (JUDGEMENT) | a2ui-bricks-v1 | 3/3 | a2ui-bricks-v1 x3 |
| B8 | cross | a2ui-charts-v1 | 3/3 | a2ui-charts-v1 x3 |
| X1 | cross | a2ui-charts-v1 | 3/3 | a2ui-charts-v1 x3 |
| X2 | cross | a2ui-atoms-v1 | 3/3 | a2ui-atoms-v1 x3 |
| X3 | cross | a2ui-learning-v1 | 3/3 | a2ui-learning-v1 x3 |
| X4 | cross | a2ui-aviation-v1 | 3/3 | a2ui-aviation-v1 x3 |
| X5 | cross | a2ui-ops-v1 | 3/3 | a2ui-ops-v1 x3 |
| X6 | cross | a2ui-marketing-v1 | 3/3 | a2ui-marketing-v1 x3 |
| X7 | null | None | 3/3 | None x3 |
| X8 | judgement (JUDGEMENT) | a2ui-marketing-v1 / a2ui-display-v1 | 3/3 | a2ui-marketing-v1 x3 |

JUDGEMENT cells, counts only (B7 accept bricks, note in key; X8 accept marketing or display):

| brief | n | in accept set | routed |
|---|---|---|---|
| B7 | 3 | 3/3 | a2ui-bricks-v1 x3 |
| X8 | 3 | 3/3 | a2ui-marketing-v1 x3 |

Downstream (offline, NOT a model call in this condition). B-briefs routed to a2ui-bricks-v1 reuse the measured P Express reply of the same repeat (labelled REUSED); scores are the P key scores (B1-B6 atom F1; B7/B8 refusal pass):

| brief | routed to bricks | REUSED P score mean over those | other routes |
|---|---|---|---|
| B1 | 3/3 | 1.0 | agent step not run: 0 |
| B2 | 3/3 | 1.0 | agent step not run: 0 |
| B3 | 3/3 | 1.0 | agent step not run: 0 |
| B4 | 3/3 | 1.0 | agent step not run: 0 |
| B5 | 3/3 | 1.0 | agent step not run: 0 |
| B6 | 3/3 | 1.0 | agent step not run: 0 |
| B7 | 3/3 | 1.0 | agent step not run: 0 |
| B8 | 0/3 | None | agent step not run: 3 |

Tokens and seconds (router calls): input 1768.5, output 42.5, request secs 1.7 (means).

