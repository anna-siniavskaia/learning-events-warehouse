CREATE TABLE learning_events (
    source_id bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
    event_id char(36) NOT NULL UNIQUE,
    learner_id varchar(32) NOT NULL,
    event_type varchar(32) NOT NULL,
    content_id varchar(32) NOT NULL,
    occurred_at datetime(6) NOT NULL,
    recorded_at datetime(6) NOT NULL,
    payload json NOT NULL,
    CHECK (event_type IN ('exercise_completed', 'text_read', 'placement_completed')),
    CHECK (recorded_at >= occurred_at)
);
