# Metric definitions

All dates are derived from `occurred_at` in UTC. A late event contributes to the date when it happened, regardless of its MySQL insertion time or PostgreSQL `loaded_at`.

| Field | Definition | Interpretation |
| --- | --- | --- |
| `active_learners` | Distinct `learner_id` values with any event that day | Activity among fictional learners, not registered users |
| `exercises_completed` | Count of `exercise_completed` events | Each event is one completion |
| `placement_tests` | Count of `placement_completed` events | Each event is one finished placement test |
| `texts_read` | Count of `text_read` events | Each event is one recorded reading session |
| `reading_minutes` | Sum of `duration_seconds` for reading events divided by 60, rounded to 2 decimals | Session time; no claim about comprehension |
| `average_exercise_score` | Average `score` among `exercise_completed` events, rounded to 2 decimals | `NULL` when no exercises were completed that day |

`mart.level_activity` groups event counts and distinct learners by event date and CEFR `level` supplied in the event payload. Its average score uses exercise events only. The level is an event attribute, not a verified or current learner proficiency.

The operational load-delay query measures `loaded_at - recorded_at` in minutes. Synthetic source timestamps are historical, so its absolute values are not a production latency benchmark. The query demonstrates where this operational measure belongs; it does not establish a service-level objective.

The input is generated fiction. These metrics verify pipeline behavior and illustrate a semantic model; they do not describe actual language learners.
