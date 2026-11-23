CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS etl;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE raw.learning_events (
    event_id uuid PRIMARY KEY,
    source_id bigint NOT NULL UNIQUE CHECK (source_id > 0),
    learner_id text NOT NULL,
    event_type text NOT NULL
        CHECK (event_type IN ('exercise_completed', 'text_read', 'placement_completed')),
    content_id text NOT NULL,
    occurred_at timestamptz NOT NULL,
    recorded_at timestamptz NOT NULL,
    payload jsonb NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (recorded_at >= occurred_at)
);

CREATE TABLE etl.watermarks (
    pipeline_name text PRIMARY KEY,
    last_source_id bigint NOT NULL DEFAULT 0 CHECK (last_source_id >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO etl.watermarks (pipeline_name, last_source_id)
VALUES ('learning_events', 0);
