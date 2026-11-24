# Integration verification, 18 November 2026

The following was run locally with MySQL 8.0, PostgreSQL 16, and the Dockerized Python runner:

1. `docker compose run --build --rm runner sh scripts/run_demo.sh` on empty volumes generated and synchronized 100 events; all seven tests present at that stage passed.
2. Repeating the demo synchronized **0** new events, confirming idempotent source loading and watermark behavior.
3. Generating ten additional events with seed 43, loading them, and syncing with batch size 4 moved **10** events. All ten had an `occurred_at` older than the latest event from the first batch.
4. Direct SQL checks returned **110** source rows, **110** raw rows, and watermark **210**. The MySQL auto-increment value contains gaps because duplicate insert attempts consume IDs; the loader handles gaps.
5. The final Docker demo reconciled all **110** source and warehouse `(source_id, event_id)` pairs, confirmed the watermark, and passed **9** unit tests.

At this stage, the ingestion path and replay were verified on the fixture. The dimensional mart and expanded quality checks were added and verified in the later runs below.

## Dimensional mart verification, 18 November 2026

After adding the mart tables and seven-day fixture, fresh Docker volumes produced **100** raw rows and **100** fact rows. The mart check compared fact attributes with raw events, learner first-seen dates, daily event totals, and the mart watermark. The first run passed all **9** then-existing unit tests. A replay built **0** new facts.

Ten seed-43 events were then loaded in batches of four. All ten occurred before the latest event in the first source batch. The mart built ten additional facts, reconciled **110** source/raw/fact rows, and advanced its own watermark to **110**. One existing learner's first-seen date moved backward because of a late event; the quality check passed. The daily view contained seven dates, 1–7 November. For 1 November after the late batch, it reported **14** active learners, **5** completed exercises, **4** placement tests, and **7** reading sessions.

After adding explicit changed-duplicate rejection and mart transaction tests, a further replay processed **0** source rows and built **0** facts. The final Docker run passed **13** unit tests and both database checks.

The recovery script inserted one raw event with score **999**, above the fact table's allowed maximum. The mart build failed on its check constraint, its watermark remained **110**, and the attempted learner dimension and fact row were absent. The script removed the temporary raw event; direct SQL then showed **110** raw rows, **110** facts, and mart watermark **110**.

## Local rehearsal of the CI workflow

With the three direct Python dependencies pinned to versions used in the successful Docker build, a fresh lab again produced **100** events across **7** event dates and passed **13** tests. An exact fixture assertion checked the initial 100 raw/fact rows; the replay processed zero new events. After ten late events, the exact assertion checked **110** rows, ten late arrivals, and one earlier first-seen event for an existing learner. The rollback demonstration and SQL query pack also passed. The GitHub-hosted workflow remains unverified until the repository is uploaded.

The one-command bootstrap was added afterward. Unit tests verified that it creates three distinct random passwords in an ignored `.env` with mode `0600`, reuses an existing file without changing it, and rejects example or incomplete credentials. In this managed environment, the nested Docker CLI call from Python was blocked by the sandbox; the equivalent Docker Compose command was run directly with the newly generated `.env` on fresh volumes and processed **100** events. A replay processed **0** new events. All **16** tests at that stage passed in the Docker runner. The wrapper's end-to-end invocation still needs confirmation in an unrestricted terminal.

The event contract was tightened to pair each event type with its content ID prefix. Docker validation accepted all 100 generated events and rejected mismatched content IDs, an out-of-range score, and a zero reading duration. The full Docker replay still reconciled 100 source/raw/fact rows and passed **19** tests.

On 20 November, mart reconciliation was extended from fact and learner-date checks to exact learner and content dimension membership. Temporary extra learner and content members were detected and rolled back by the recovery demonstration. Three focused unit tests cover the successful path and both drift failures. The complete Docker replay then processed zero new source rows, reconciled 100 raw and fact rows, and passed all **22** tests.

On 21 November, the integration assertion was tightened to compare all seven rows of `mart.daily_activity`, including active learners, event-type counts, reading minutes, and average exercise score. Exact fixtures cover both the initial 100-event state and the 110-event state after ten late arrivals. Two unit tests prove that the complete result passes and that a metric change is rejected even when every row count remains unchanged. The documented 110-event result is in [sample-results.md](sample-results.md).

On 22 November, the same exact reconciliation was extended to every `(event_date, level)` row in `mart.level_activity`. Fixtures now pin event counts, distinct active learners, exercise-score averages, and `NULL` score semantics for both the 100-event and 110-event states. Two additional tests verify the complete result and reject a changed level metric without relying on row counts.

On 23 November, the reviewed 34-file snapshot was published to the private `anna-siniavskaia/learning-events-warehouse` repository. GitHub confirmed `main`, the README, and `.github/workflows/verify.yml`; hosted CI remains pending until the first workflow run completes.

## Operational health snapshot, 24 November 2026

`src/health_report.py` now emits one JSON object with source, raw, and fact counts; source and warehouse maxima; ingestion and mart watermarks; and both lag values. A healthy 110-event late-arrival state reports zero lag. Unit coverage also verifies a degraded state with pending ingestion and mart rows, plus an explicit failure for a missing watermark. The command is part of `scripts/run_demo.sh`, so the same assertion runs in local demos and hosted CI.

Private pull request [#1](https://github.com/anna-siniavskaia/learning-events-warehouse/pull/1) supplied the first hosted end-to-end verification. The initial run exposed that MySQL returns `max(source_id)` as a decimal value, which the JSON encoder rejected. The health report now normalizes database numeric types and includes a decimal regression fixture. Workflow run 5 then passed the fresh build, idempotent replay, late-event load, rollback recovery, sample queries, and disposable database cleanup before the pull request was squash-merged.

## Tracked-file review, 19 November 2026

`git ls-files` returned **32** source, SQL, contract, workflow, test, and documentation files. The local `.env` and generated JSONL data were not tracked; `.env.example` contained only three explicit `replace-with-...` placeholders. A tracked-file scan found no API key, access token, or private-key marker, and no project file outside generated data exceeded **1 MiB**. The worktree was clean before this verification record was added.
