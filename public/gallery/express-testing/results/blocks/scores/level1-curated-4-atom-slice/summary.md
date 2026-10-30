| model | cond | format | n | compile rate | mean F1 (B1-B7) | B3 honest | B8 pass | brick ok (B5-B7, validator ran) | mean in tok | mean out tok | mean req s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sonnet-5-5 | B4 | express | 24 | 1.00 | 0.57 | 3/3 | 0/3 | 6/7 | 4671.75 | 1089.42 | 9.38 |
| sonnet-5-5 | B4 | json | 24 | 0.88 | 0.57 | 2/3 | 0/3 | 1/4 | 7251.75 | 1192.0 | 9.54 |

Per brief (mean score; B8 = pass rate):

| model | cond | format | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 |
|---|---|---|---|---|---|---|---|---|---|---|
| sonnet-5-5 | B4 | express | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 |
| sonnet-5-5 | B4 | json | 1.0 | 1.0 | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 |
