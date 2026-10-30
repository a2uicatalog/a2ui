# Router comparison (offline scoring)

## Set R (16 briefs). Per-group correct / replies; groups never blended. multi and judgement: any accepted catalogue counts.

| router | block | cross | null | judgement | mean ms/route | mean input tokens | mean output tokens | replies |
|---|---|---|---|---|---|---|---|---|
| hybrid | 1/6 | 7/7 | 1/1 | 2/2 | 0.942 | 0 | 0 | 16 |
| lexical | 6/6 | 4/7 | 1/1 | 2/2 | 0.044 | 0 | 0 | 16 |
| lexical_max | 5/6 | 7/7 | 1/1 | 1/2 | 0.858 | 0 | 0 | 16 |
| tags | 0/6 | 5/7 | 1/1 | 1/2 | 0.113 | 0 | 0 | 16 |
| sonnet-5-5 | 18/18 | 21/21 | 3/3 | 6/6 | 1656 (1.66 s) | 1768 | 43 | 48 |
| jev | 15/18 | 21/21 | 3/3 | 6/6 | 191.250 | 1456 | 216 | 48 |

Wrong replies per router (brief: routed instead; for repeated replies, count in brackets):

- hybrid: B2: a2ui-aviation-v1; B3: a2ui-marketing-v1; B4: a2ui-aviation-v1; B5: a2ui-charts-v1; B6: a2ui-charts-v1
- lexical: B8: a2ui-ops-v1; X2: a2ui-google-workspace-live-v1; X5: a2ui-atoms-v1
- lexical_max: B4: None; X8: a2ui-ops-v1
- tags: B1: None; B2: a2ui-aviation-v1; B3: a2ui-presentation-v1; B4: a2ui-aviation-v1; B5: a2ui-embeds-v1; B6: a2ui-embeds-v1; B7: a2ui-presentation-v1; X2: a2ui-marketing-v1; X5: a2ui-charts-v1
- sonnet-5-5: none
- jev: B4: None [x3]

## Set R2 (24 briefs). Per-group correct / replies; groups never blended. multi and judgement: any accepted catalogue counts.

| router | clear | null | multi | judgement | mean ms/route | mean input tokens | mean output tokens | replies |
|---|---|---|---|---|---|---|---|---|
| hybrid | 8/12 | 0/3 | 4/4 | 5/5 | 1.071 | 0 | 0 | 24 |
| lexical | 7/12 | 3/3 | 4/4 | 3/5 | 0.048 | 0 | 0 | 24 |
| lexical_max | 4/12 | 2/3 | 4/4 | 4/5 | 0.954 | 0 | 0 | 24 |
| tags | 7/12 | 0/3 | 4/4 | 5/5 | 0.123 | 0 | 0 | 24 |
| sonnet-5-5 | 36/36 | 9/9 | 10/12 | 11/15 | 1953 (1.95 s) | 1770 | 78 | 72 |
| jev | 36/36 | 9/9 | 12/12 | 12/15 | 191.806 | 1457 | 216 | 72 |

Wrong replies per router (brief: routed instead; for repeated replies, count in brackets):

- hybrid: Y13: None; Y15: a2ui-atoms-v1; Y19: None; Y20: a2ui-learning-v1; Y22: a2ui-learning-v1; Y23: a2ui-ops-v1; Y24: a2ui-charts-v1
- lexical: Y4: None; Y13: None; Y15: None; Y16: None; Y17: None; Y18: None; Y19: None
- lexical_max: Y4: None; Y5: a2ui-effects-v1; Y7: a2ui-ops-v1; Y13: None; Y14: None; Y15: None; Y16: None; Y17: None; Y19: None; Y24: a2ui-charts-v1
- tags: Y13: None; Y14: None; Y15: a2ui-charts-v1; Y19: None; Y20: a2ui-learning-v1; Y22: a2ui-learning-v1; Y23: a2ui-google-workspace-live-v1; Y24: a2ui-charts-v1
- sonnet-5-5: Y1: MALFORMED [x3]; Y4: MALFORMED; Y12: MALFORMED [x2]
- jev: Y6: None [x3]

multi briefs, non-LLM top-2 contains ALL needed catalogues (what a two-slice router could do): hybrid 2/4, lexical 4/4, lexical_max 3/4, tags 0/4

## Set tune (12 briefs). Per-group correct / replies; groups never blended. multi and judgement: any accepted catalogue counts.

| router | clear | null | mean ms/route | mean input tokens | mean output tokens | replies |
|---|---|---|---|---|---|---|
| hybrid | 8/10 | 1/2 | 0.904 | 0 | 0 | 12 |
| lexical | 10/10 | 2/2 | 0.043 | 0 | 0 | 12 |
| lexical_max | 10/10 | 2/2 | 0.777 | 0 | 0 | 12 |
| tags | 7/10 | 1/2 | 0.113 | 0 | 0 | 12 |

Wrong replies per router (brief: routed instead; for repeated replies, count in brackets):

- hybrid: TU1: a2ui-effects-v1; TU8: a2ui-google-workspace-live-v1; TU11: a2ui-charts-v1
- lexical: none
- lexical_max: none
- tags: TU1: a2ui-effects-v1; TU5: a2ui-presentation-v1; TU8: a2ui-google-workspace-live-v1; TU11: a2ui-charts-v1

