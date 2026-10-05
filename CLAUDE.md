# CLAUDE.md

Guidance for Claude Code working in this repo. Human-facing docs are in [README.md](README.md) (setup), [docs/learning-path.md](docs/learning-path.md) (participants) and [docs/reference.md](docs/reference.md) (tests, seeder, YAML pipelines). The design and build order are in [PLAN.md](PLAN.md).

## What this is

A local, testing-only lab for teaching OpenMetadata's catalog and data-quality features. `seed/seed.py` fills a source MySQL with fake data, a share of it deliberately bad. OpenMetadata 2.0.2 catalogs, profiles and tests it. `seed/fix_defects.py` removes the bad rows again. Phase 1 (MySQL) is built. Phase 2 (Oracle) is in progress: M4 is built (compose service, `oracle_schema.py`, `oracle_generators.py`, `seed.py --target oracle`); M5 (YAML pipelines, docs, `fix_defects.py` for Oracle) is not.

## Layout

- `compose.yml`: includes `openmetadata/docker-compose.yml` (official, pinned) merged with `openmetadata/docker-compose.override.yml`, plus `sources/docker-compose.yml`.
- `seed/`: `seed.py` (append bad and clean rows), `fix_defects.py` (delete the bad rows), `mysql_generators.py` (defects and the test that catches each), `mysql_schema.py`.
- `pipelines/mysql/`: YAML twins of the UI pipelines, including `dq_tests_*.yaml`.
- `.env` (git-ignored, holds real credentials and the ingestion-bot JWT) and `.env.example` (placeholders only).

## Rules

- **Never edit `openmetadata/docker-compose.yml`.** It is the upstream 2.0.2 release file, checksummed in the README. Lab changes go in `openmetadata/docker-compose.override.yml`.
- Phase 2 was started on the user's go-ahead (2026-10-05, M4). Do M5 only when asked. If something in PLAN.md doesn't work in practice, stop and ask; once a change is agreed, update PLAN.md to match.
- **Real credentials go only in `.env`.** Never commit it or put secrets in docs or YAML.
- **Git:** there is no `gh` CLI and no PRs. Commit, then push straight to `main` when asked. End commit messages with the Co-Authored-By line from the session's attribution instructions.
- **Defects and tests stay in sync.** If you change a defect in `mysql_generators.py`, update the matching test in `pipelines/mysql/dq_tests_*.yaml`, the test table in `docs/reference.md`, and `fix_defects.py`.
- Keep the YAML test names, the README test table and the OpenMetadata test cases identical (13 tests, suite `dqlab_mysql_suite`).

## Documentation conventions

- Write for participants: plain, short, one idea per step, and keep the three audiences apart (setup in the README, walkthrough in `docs/learning-path.md`, lookups in `docs/reference.md`).
- **AutoPilot is real and automatic.** Create & Deploy in the add-service wizard makes the browser call `apps/trigger/AutoPilotApplication` (nothing to press). It runs the Metadata agent at once, and about an hour later adds the Usage, Profiler and AutoClassification agents (provider `automation`, weekly). Its Profiler is limited to `Tier1`/`Tier2` and its AutoClassification has PII tagging on, so both need editing. Creating the service through the API or YAML does not trigger it (tested). Don't check agent lists within the first hour and conclude they don't exist.
- Describe the UI as it is in OpenMetadata 2.0.2 (for example, a logical test suite is a "Bundle Suite", and the service wizard has no Save button).
- The user does the UI checks. When a doc change depends on what the UI shows, verify it through the API where you can, and say plainly what you couldn't see.

## Working with the running stack

- UIs: OpenMetadata http://localhost:8585 (`admin@open-metadata.org` / `admin`), Airflow http://localhost:8080 (`admin` / `admin`).
- Source MySQL is on `127.0.0.1:3307` from the host and `source-mysql:3306` inside Docker.
- To inspect OpenMetadata state, log in to the REST API at `http://localhost:8585/api/v1` (`POST /users/login`, password base64-encoded) and read services, ingestion pipelines and test cases.
- A MySQL prompt in the source container: `docker compose exec source-mysql sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" dqlab'`.
- `docker compose down` keeps data; `down -v` wipes every named volume, OpenMetadata's MySQL included. Ask before wiping.

## Environment gotchas

- The user's network inspects TLS (Cisco Umbrella). Containers can't download from GitHub at runtime (`CERTIFICATE_VERIFY_FAILED`), which is why PII auto-classification stays off. On the Windows host use `curl --ssl-no-revoke` and `git -c http.schannelCheckRevoke=false` when a download fails. Expect the same problem for anything Oracle-related that downloads from GitHub.
- Windows: OpenMetadata's MySQL data must stay on a named volume. A bind mount on the case-insensitive Windows filesystem crashed InnoDB.
- Git Bash turns `/tmp/...` into a Windows path; prefix `docker` commands with `MSYS_NO_PATHCONV=1` or use PowerShell.
- The repo uses LF line endings (`.gitattributes`) so the official compose file stays byte-identical.
