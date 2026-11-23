# Learning Events Warehouse

A local Data Engineering pipeline that turns synthetic Spanish-learning activity into an analytics warehouse. No learner records from the Spanish-learning app are used. The generator produces fictional IDs and events.

## Pipeline

```text
synthetic events → MySQL source → incremental loader → PostgreSQL raw → analytics models
```

The loader advances a PostgreSQL watermark using the MySQL `source_id`, not the event timestamp. That design keeps late-arriving events in scope. Raw rows are keyed by a stable `event_id`, so replaying a batch is idempotent. The watermark and raw inserts commit in one PostgreSQL transaction. A second incremental step builds learner/content dimensions and event facts.

## Current milestone

- [x] Define the event contract in `contracts/learning_event.schema.json`.
- [x] Generate deterministic, fictional JSONL events with `src/generate_events.py`.
- [x] Define source and warehouse tables in `sql/`.
- [x] Implement source loading, incremental extraction, and transactional warehouse loading.
- [x] Define a Docker Compose setup for MySQL, PostgreSQL, and the Python runner.
- [x] Reconcile source IDs, event IDs, and the watermark across both databases.
- [x] Build dimensional tables, daily and level views, and mart quality checks.
- [x] Verify fresh builds, replays, and late events end to end.
- [x] Verify failure rollback and recovery on a disposable invalid event.
- [ ] Final review and publish the first complete version privately.

Generate 100 local events:

```bash
python3 src/generate_events.py --seed 42 --count 100 --output data/events.jsonl
```

`data/` is ignored by Git. Event timestamps are UTC. `occurred_at` is deliberately not ordered by source insertion order, so the pipeline must handle late events correctly.

## Local demo

With Docker running, run this one command from the project directory:

```bash
python3 scripts/bootstrap.py
```

The bootstrap creates an ignored `.env` with three random local passwords if needed. It then generates fictional events, loads them into MySQL, syncs new source IDs into PostgreSQL, builds the dimensional mart, checks both layers, and runs unit tests. On a fresh database, rerunning it leaves 100 rows in each layer and processes zero new events. Database volumes persist between runs; `docker compose down -v` removes them when you want a fresh lab.

Run the sample queries after the demo:

```bash
docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U pipeline -d learning -f /app/05_example_queries.sql
```

Demonstrate a failed mart refresh and clean recovery on the local lab:

```bash
docker compose run --rm runner python -m scripts.verify_recovery
```

The recovery check inserts a temporary raw event with an invalid score, confirms that the mart fact, new dimensions, and watermark all roll back, then removes that event. It leaves the valid rows in place.

The MySQL `datetime(6)` values represent UTC without an offset. The loader converts timestamp strings to UTC before insertion. The warehouse transaction locks its watermark row, inserts or verifies each source row, then advances the watermark. A conflicting event aborts the transaction. This prevents a successful watermark update for a failed batch.

See [architecture and recovery](docs/architecture.md), [metric definitions](docs/metrics.md), [reproducible sample results](docs/sample-results.md), [integration verification](docs/verification.md), and the [private release checklist](docs/release-checklist.md) for the data flow, retry behavior, observed checks, and remaining publication gates.

## Automated verification

The [GitHub Actions workflow](.github/workflows/verify.yml) will run on pushes and pull requests after the private repository is created. It builds empty databases, checks an identical replay, loads ten late events, asserts every daily and CEFR-level metric before and after that batch, tests rollback, and executes the sample queries. The same sequence was run locally; the hosted workflow has not run yet because this project is not on GitHub.
