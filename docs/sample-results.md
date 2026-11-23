# Reproducible sample results

The table below is the exact `mart.daily_activity` result after the deterministic
100-event seed-42 batch and the ten deliberately late seed-43 events. The CI
fixture compares every value, not only row counts, so a changed metric definition
or an incorrect late-event rebuild fails the pipeline verification.

| Event date | Active learners | Exercises | Placement tests | Texts read | Reading minutes | Average exercise score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-11-01 | 14 | 5 | 4 | 7 | 41.45 | 51.20 |
| 2026-11-02 | 20 | 9 | 6 | 8 | 53.28 | 43.56 |
| 2026-11-03 | 12 | 6 | 5 | 2 | 14.65 | 52.17 |
| 2026-11-04 | 18 | 3 | 11 | 6 | 42.57 | 47.00 |
| 2026-11-05 | 12 | 4 | 3 | 5 | 34.32 | 61.25 |
| 2026-11-06 | 7 | 4 | 2 | 2 | 11.42 | 76.75 |
| 2026-11-07 | 17 | 7 | 6 | 5 | 51.38 | 43.86 |

Late events are attributed to their `occurred_at` date. For example, the
1 November aggregate changes from 13 to 14 active learners and from 58.25 to
51.20 average exercise score after the late batch. This is why the mart is
recomputed by event date rather than by warehouse load date.

These figures describe generated fiction and demonstrate pipeline semantics;
they are not learner or product analytics.
