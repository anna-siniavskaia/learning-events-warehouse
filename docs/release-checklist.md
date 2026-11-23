# Private release checklist

Use this checklist for the first private GitHub release. Record evidence instead of checking a box from memory.

## Local evidence

- [x] All generated learner, content, and event identifiers are fictional and deterministic.
- [x] `.env` and generated JSONL files are ignored by Git.
- [x] A fresh Docker build loaded 100 events into MySQL, PostgreSQL raw, and the dimensional fact table.
- [x] An unchanged replay processed zero new source rows and built zero new facts.
- [x] Ten late events were loaded by `source_id` and changed historical aggregates without being skipped.
- [x] The recovery demonstration preserved both watermarks when a mart refresh failed.
- [x] Mart quality checks detect missing, extra, or changed learner and content dimension members.
- [x] Exact daily and CEFR-level metric fixtures cover the initial and late-event states across all seven event dates.
- [x] Contract validation rejects invalid scores, durations, and event/content ID combinations.
- [x] The full Docker replay passed 22 tests on 20 November 2026.

See [verification.md](verification.md) for commands, fixture counts, and limitations.

## Before the first push

- [ ] Run `python3 scripts/bootstrap.py` once in an unrestricted local terminal and record the result.
- [x] Review `git status` and the complete tracked-file list for credentials, generated data, and large files.
- [ ] Create the GitHub repository as private and push `main` on the planned release date.

## After the first push

- [ ] Confirm the GitHub Actions workflow passes from empty database volumes.
- [ ] Open the README links and verify that the architecture, metrics, verification, and checklist pages render.
- [ ] Keep the repository private until Anna makes a separate visibility decision.
