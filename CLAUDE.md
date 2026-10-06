# CLAUDE.md

Guidance for Claude Code working in this repo. Human-facing docs are in [README.md](README.md) (setup), [docs/learning-path.md](docs/learning-path.md) (participants) and [docs/reference.md](docs/reference.md) (tests, seeder, agents). The design and build order are in [PLAN.md](PLAN.md).

## What this is

A local, testing-only lab for teaching OpenMetadata's catalog and data-quality features. `seed/seed.py` fills the source databases (MySQL, and Oracle behind a compose profile) with fake data, a share of it deliberately bad. OpenMetadata 2.0.2 catalogs, profiles and tests it. `seed/fix_defects.py` removes the bad rows again. Phase 1 (MySQL) and Phase 2 (Oracle, opt-in under the `oracle` compose profile) are both built (M1 to M5).

The course goal is broader than data quality: participants should understand OpenMetadata as a whole and be able to show evidence for the National Data Index (NDI) maturity assessment (42 questions in 14 domains, Level 0 to 5). The source is SDAIA's published NDI material, kept in `docs/` (the National Data Index document, v1.1: 42 maturity questions with levels and acceptance evidence; and the Operational Excellence handbook and FAQ) and linked from https://sdaia.gov.sa/en/Research/Pages/NationalDataIndex.aspx. The map from each question to what OpenMetadata can show is the "NDI evidence map" in docs/reference.md; items G1 to G7 in docs/learning-path.md produce that evidence. Evidence is cumulative by level: Level 3 is the tool in use, Level 4 a KPI monitoring report, Level 5 continuous improvement and automation.

## Layout

- `compose.yml`: includes `openmetadata/docker-compose.yml` (official, pinned) merged with `openmetadata/docker-compose.override.yml`, plus `sources/docker-compose.yml`.
- `docs/`: `learning-path.md`, `reference.md`, and SDAIA's NDI documents (PDF) that the NDI evidence map is based on.
- `seed/`: `seed.py` (append bad and clean rows), `fix_defects.py` (delete the bad rows), `mysql_generators.py` and `oracle_generators.py` (defects and the test that catches each), `mysql_schema.py`, `oracle_schema.py`.
- `.env` (git-ignored, holds real credentials) and `.env.example` (placeholders only).

## Rules

- **Never edit `openmetadata/docker-compose.yml`.** It is the upstream 2.0.2 release file, checksummed in the README. Lab changes go in `openmetadata/docker-compose.override.yml`.
- If something in PLAN.md doesn't work in practice, stop and ask; once a change is agreed, update PLAN.md to match.
- **Real credentials go only in `.env`.** Never commit it or put secrets in docs.
- **Git:** there is no `gh` CLI and no PRs. Commit, then push straight to `main` when asked. End commit messages with the Co-Authored-By line from the session's attribution instructions.
- **Defects and tests stay in sync.** If you change a defect in `mysql_generators.py`, update the matching test in the test tables in `docs/reference.md`, and `fix_defects.py`. The same goes for `oracle_generators.py`.
- Keep the NDI evidence map (docs/reference.md), the `NDI evidence` line on each learning-path item and items G1 to G7 consistent with each other. Don't invent a new database for NDI examples: the course uses the existing e-commerce and HR data. Where something is a policy and not a tool feature, say so; don't stretch OpenMetadata to cover it.
- Keep the test names in `docs/reference.md`, the generators' `DEFECTS` and the OpenMetadata test cases identical (MySQL: 13 tests, suite `dqlab_mysql_suite`; Oracle: 12 tests, suite `dqlab_oracle_suite`).

## Documentation conventions

- Write for participants: plain, short, one idea per step, and keep the three audiences apart (setup in the README, walkthrough in `docs/learning-path.md`, lookups in `docs/reference.md`).
- **AutoPilot is real and automatic.** Create & Deploy in the add-service wizard makes the browser call `apps/trigger/AutoPilotApplication` (nothing to press). Within about two minutes it creates Metadata, Lineage, Usage, Profiler and AutoClassification agents (provider `automation`, weekly) and runs the first three: Metadata succeeds, Lineage fails on MySQL (the lab user can't read `mysql.general_log`), Usage finds nothing. Profiler and AutoClassification are created but wait for Sunday, so they need editing and a click on Run. Its Profiler is limited to `Tier1`/`Tier2` and its AutoClassification has PII tagging on and sample data off. Creating the service through the API does not trigger it (tested). Verified in the UI on MySQL; Oracle not yet.
- Describe the UI as it is in OpenMetadata 2.0.2 (for example, a logical test suite is a "Bundle Suite", and the service wizard has no Save button).
- The user does the UI checks. When a doc change depends on what the UI shows, verify it through the API where you can, and say plainly what you couldn't see.

## Working with the running stack

- UIs: OpenMetadata http://localhost:8585 (`admin@open-metadata.org` / `admin`), Airflow http://localhost:8080 (`admin` / `admin`).
- Source MySQL is on `127.0.0.1:3307` from the host and `source-mysql:3306` inside Docker. Source Oracle (profile `oracle`) is on `127.0.0.1:1521`, service `XEPDB1`, and `source-oracle:1521` inside Docker.
- To inspect OpenMetadata state, log in to the REST API at `http://localhost:8585/api/v1` (`POST /users/login`, password base64-encoded) and read services, ingestion pipelines and test cases.
- A MySQL prompt in the source container: `docker compose exec source-mysql sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" dqlab'`.
- `docker compose down` keeps data; `down -v` wipes every named volume, OpenMetadata's MySQL included. Ask before wiping. Always add `--profile oracle` to `down`: without it Compose leaves the Oracle container running and keeps its volume.

## Environment gotchas

- There is no pipeline YAML in this repo, on purpose: it's not supported and the user doesn't want to maintain it. Services, agents and tests are created in the UI (or, for verification, the REST API). Agents are ingestion pipelines; see "Agents and AutoPilot" in docs/reference.md.
- Oracle: OpenMetadata's connector needs dictionary access (`seed.py --target oracle --init` grants `SELECT ANY DICTIONARY`), which exposes `SYS`, so every Oracle pipeline needs the schema filter `(?i)^dqlab$`. OpenMetadata lowercases the schema, column and view names (table `dqlab.EMPLOYEES` has column `emp_id`), so test cases need lowercase column names. A test case created wrongly is reused with `forceUpdate: false`: delete it first.
- The user's network inspects TLS (Cisco Umbrella). Containers can't download from GitHub at runtime (`CERTIFICATE_VERIFY_FAILED`), which is why PII auto-classification stays off. On the Windows host use `curl --ssl-no-revoke` and `git -c http.schannelCheckRevoke=false` when a download fails. Expect the same problem for anything Oracle-related that downloads from GitHub.
- Windows: OpenMetadata's MySQL data must stay on a named volume. A bind mount on the case-insensitive Windows filesystem crashed InnoDB.
- Git Bash turns `/tmp/...` into a Windows path; prefix `docker` commands with `MSYS_NO_PATHCONV=1` or use PowerShell.
- The repo uses LF line endings (`.gitattributes`) so the official compose file stays byte-identical.
