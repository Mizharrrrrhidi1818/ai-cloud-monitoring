# Testing and Evaluation Evidence

All figures below are historical user-provided outputs; no live query was performed while composing these documents.

| Test or check | Reported result | Scope and limitation |
|---|---|---|
| Alert rules | 9 passed | Previous logic (AI anomaly **AND** threshold) |
| Alert cooldown | 5 passed | Python cooldown helper |
| PostgreSQL alert integration | 4 passed | Local temp table and rollback |
| VPS controlled alert integration | 5 passed | VPS temp table and rollback; earlier rules |
| Candidate model compatibility | 6 passed | Windows only, not Docker |
| Host collection data quality | 11,804/11,804 valid | One exported VPS snapshot |
| Isolation Forest held-out VPS data | 2,289 normal, 72 anomaly | **No incident labels** |
| Synthetic scenario evaluation | 4/6 matched expectations | Not real-world accuracy |

## Actual VPS collection snapshot

- First timestamp: `2026-11-04 16:14:02.276751`
- Last timestamp: `2026-11-05 08:58:02.800717`
- Duration: `16:44:00.523966`
- Median interval: `5.008872` seconds
- Gaps over 15 seconds: `1`
- Missing records, duplicate IDs, out-of-range utilization: all `0`.

| Feature | Mean | Std dev | Min | Max |
|---|---:|---:|---:|---:|
| CPU % | 3.30 | 3.12 | 0.00 | 52.30 |
| RAM % | 58.18 | 0.78 | 45.20 | 67.60 |
| Disk % | 46.81 | 0.28 | 41.20 | 46.90 |

## Candidate model held-out evaluation

- Chronological split: 9,443 train / 2,361 test.
- Anomaly frequency: 72 / 2,361 = 3.05%.
- Reported most unusual observation: 2026-11-05 07:49:30, CPU 26.7%, RAM 61.2%, disk 46.9%, score -0.140983.
- Synthetic scenario agreement: four of six; failures include a 99% disk reading classified normal and 35% CPU classified anomalous despite nominal normal expectation.

## Important caveat

A ratio of predicted anomalies is not a measure of classifier accuracy; precision/recall/F1 require carefully validated incident labels. Current ML evaluation remains exploratory, with an offline VPS-trained candidate separate from the production model. New threshold-only alert rules, when tested and deployed, should have separate release evidence; older test totals must not be relabeled as tests of the new design.
