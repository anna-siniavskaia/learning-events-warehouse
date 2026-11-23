CREATE VIEW mart.daily_activity AS
SELECT
    event_date,
    count(DISTINCT learner_id) AS active_learners,
    count(*) FILTER (WHERE event_type = 'exercise_completed') AS exercises_completed,
    count(*) FILTER (WHERE event_type = 'placement_completed') AS placement_tests,
    count(*) FILTER (WHERE event_type = 'text_read') AS texts_read,
    round(sum(duration_seconds) FILTER (WHERE event_type = 'text_read') / 60.0, 2)
        AS reading_minutes,
    round(avg(score) FILTER (WHERE event_type = 'exercise_completed'), 2)
        AS average_exercise_score
FROM mart.fct_learning_event
GROUP BY event_date;

CREATE VIEW mart.level_activity AS
SELECT
    event_date,
    level,
    count(*) AS events,
    count(DISTINCT learner_id) AS active_learners,
    round(avg(score) FILTER (WHERE event_type = 'exercise_completed'), 2)
        AS average_exercise_score
FROM mart.fct_learning_event
GROUP BY event_date, level;
