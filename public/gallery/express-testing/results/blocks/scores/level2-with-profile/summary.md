Condition P (profiled block agent, slice P3). Tests COMPLIANCE with the profile (partly by design), not discovery. Matching and refusal briefs are reported separately; no blended means.

| model | format | n | compile rate | mean F1 (B1-B6) | refusal pass (B7+B8) | invented fields (replies / total) | B3 pass | brick validator B5/B6 (ok / ran; named shape; no list) |
|---|---|---|---|---|---|---|---|---|
| sonnet-5-5 | express | 24 | 1.00 | 1.0 | 6/6 | 0 / 0 | 3/3 | 1 / 3; 3; 0 |

Tokens and request seconds, matching briefs (B1-B6) and refusal briefs (B7, B8) separately:

| model | format | group | n | mean in tok | mean out tok | mean req s |
|---|---|---|---|---|---|---|
| sonnet-5-5 | express | matching B1-B6 | 18 | 3603.83 | 640.72 | 6.11 |
| sonnet-5-5 | express | refusal B7+B8 | 6 | 3607.5 | 119.17 | 2.0 |

Per brief (mean score; B7/B8 = refusal pass rate):

| model | format | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 |
|---|---|---|---|---|---|---|---|---|---|
| sonnet-5-5 | express | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
