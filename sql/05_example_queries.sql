-- Daily activity in event time (UTC); late events appear on their occurrence date.
SELECT * FROM mart.daily_activity ORDER BY event_date;

-- Score by CEFR level and date. NULL means no exercise was completed in that group.
SELECT * FROM mart.level_activity ORDER BY event_date, level;

-- Operational latency from source recording to warehouse loading.
SELECT
    event_type,
    count(*) AS events,
    round(avg(extract(epoch FROM loaded_at - recorded_at)) / 60.0, 2)
        AS average_load_delay_minutes
FROM raw.learning_events
GROUP BY event_type
ORDER BY event_type;
