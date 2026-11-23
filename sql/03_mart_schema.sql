CREATE TABLE mart.dim_learner (
    learner_id text PRIMARY KEY,
    first_seen_at timestamptz NOT NULL
);

CREATE TABLE mart.dim_content (
    content_id text PRIMARY KEY,
    event_type text NOT NULL,
    CHECK (
        (event_type = 'exercise_completed' AND content_id ~ '^exercise-[0-9]{3}$') OR
        (event_type = 'text_read' AND content_id ~ '^text-[0-9]{3}$') OR
        (event_type = 'placement_completed' AND content_id ~ '^placement-[0-9]{3}$')
    )
);

CREATE TABLE mart.fct_learning_event (
    event_id uuid PRIMARY KEY,
    source_id bigint NOT NULL UNIQUE,
    learner_id text NOT NULL REFERENCES mart.dim_learner (learner_id),
    content_id text NOT NULL REFERENCES mart.dim_content (content_id),
    event_type text NOT NULL,
    event_date date NOT NULL,
    occurred_at timestamptz NOT NULL,
    level text NOT NULL CHECK (level IN ('A1', 'A2', 'B1', 'B2')),
    score integer CHECK (score BETWEEN 0 AND 100),
    duration_seconds integer CHECK (duration_seconds > 0),
    CHECK (
        (event_type = 'text_read' AND score IS NULL AND duration_seconds IS NOT NULL) OR
        (event_type IN ('exercise_completed', 'placement_completed')
            AND score IS NOT NULL AND duration_seconds IS NULL)
    )
);

CREATE TABLE mart.refresh_state (
    model_name text PRIMARY KEY,
    last_source_id bigint NOT NULL DEFAULT 0 CHECK (last_source_id >= 0),
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO mart.refresh_state (model_name, last_source_id)
VALUES ('learning_events', 0);
