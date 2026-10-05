# openmetadata-dq-lab

A local, testing-only lab for learning OpenMetadata's catalog and data-quality features hands-on. A seeder fills a source database with fake data on demand, a configurable share of it deliberately bad. OpenMetadata catalogs, profiles and tests that database, and the bad rows surface as failed tests you can triage.

| Phase | Source | Domain | Status |
|---|---|---|---|
| 1 | MySQL 8.4 | E-commerce: products, customers, orders | Ready |
| 2 | Oracle 21c XE | Legacy HR/payroll: views, lineage, legacy quirks | Planned |

Nothing is scheduled: seeding and every OpenMetadata pipeline run when you trigger them, so an instructor controls the pace. Out of scope: production hardening, auth/SSO, backups, HA, Kubernetes.

## Where to read what

| You are | Read |
|---|---|
| Setting up the lab | This file |
| A participant | [docs/learning-path.md](docs/learning-path.md) |
| Looking up the tests, seeder flags or YAML pipelines | [docs/reference.md](docs/reference.md) |
| Claude Code working on the repo | [CLAUDE.md](CLAUDE.md) |

## How it fits together

```
 your machine                      Docker project "dqlab", network app_net
 ------------                      ---------------------------------------------------------
                                   openmetadata/docker-compose.yml (official, unmodified)
 browser  -- localhost:8585 -->      openmetadata-server --> mysql (OpenMetadata's own), elasticsearch
 browser  -- localhost:8080 -->      ingestion: Airflow + the OpenMetadata ingestion framework
                                       |  runs the agents (metadata, auto classification,
                                       |  profiler, tests) against source-mysql:3306
                                       v
                                   sources/docker-compose.yml
 seed/seed.py -- 127.0.0.1:3307 -->  source-mysql: MySQL 8.4, database dqlab
```

- `compose.yml` includes both compose files. `openmetadata/docker-compose.yml` is the official release file, pinned and never edited (see [Pinned OpenMetadata version](#pinned-openmetadata-version)). The one change the lab needs, a named volume for OpenMetadata's MySQL data, lives in `openmetadata/docker-compose.override.yml`, which `compose.yml` merges in.
- `source-mysql` is separate from OpenMetadata's internal MySQL: its own service, host port (3307) and volume. It joins OpenMetadata's network, so OpenMetadata reaches it as `source-mysql:3306`.
- `seed/seed.py` runs on your machine and appends data through `127.0.0.1:3307`. `seed/fix_defects.py` removes the bad rows again.
- `pipelines/mysql/` holds YAML versions of the UI pipelines, as reference and fallback.

## Prerequisites

- Docker with Compose v2.20 or newer (the root file uses `include:`).
- Docker memory: 8 GB and 4 vCPU recommended (Docker Desktop: Settings > Resources). Phase 1 idles at about 5 GB.
- About 10 GB of disk for images.
- Python 3.10 or newer for the seeder.
- Free host ports: 3306 (OpenMetadata's MySQL), 3307, 8080, 8585, 8586, 9200, 9300.

## Quickstart (Phase 1)

1. Create your `.env` (git-ignored; lab credentials live here):

   ```sh
   cp .env.example .env            # PowerShell: Copy-Item .env.example .env
   ```

2. Start OpenMetadata and the source database:

   ```sh
   docker compose up -d
   ```

   The first start pulls about 9 GB of images, then OpenMetadata takes a few minutes to migrate and boot. It's ready when http://localhost:8585 shows the login page and `docker compose ps` lists `openmetadata_server` as healthy.

   | UI | URL | Login |
   |---|---|---|
   | OpenMetadata | http://localhost:8585 | `admin@open-metadata.org` / `admin` |
   | Airflow (bundled pipeline runner) | http://localhost:8080 | `admin` / `admin` |

3. Install the seeder:

   ```sh
   python -m venv .venv
   source .venv/bin/activate       # PowerShell: .venv\Scripts\Activate.ps1
   pip install -r seed/requirements.txt
   ```

4. Seed a clean baseline, a week of data with no bad rows:

   ```sh
   python seed/seed.py --init --bad-rate 0 --days 7
   ```

5. Hand over to the participants: [docs/learning-path.md](docs/learning-path.md).

## Resetting

To start again with fresh source tables, leaving OpenMetadata as it is:

```sh
docker compose rm --stop --force source-mysql
docker volume rm dqlab_source-mysql-data
docker compose up -d --wait source-mysql
python seed/seed.py --init --bad-rate 0 --days 7
```

OpenMetadata keeps its catalog, profiles and test history for the `dqlab_mysql` tables. For a clean catalog too, delete the service in Settings > Services > Databases > `dqlab_mysql` (hard delete) and add it again.

To reset everything:

```sh
docker compose down -v
```

`down -v` removes all the named volumes: source data, OpenMetadata's MySQL, Elasticsearch and Airflow. Use plain `docker compose down` to stop the lab and keep your data.

## Troubleshooting

- **`required variable SOURCE_MYSQL_ROOT_PASSWORD is missing a value`**: create `.env` from `.env.example`, in the repo root.
- **`the attribute 'version' is obsolete`**: a warning about the official OpenMetadata compose file. It's harmless and the file stays unmodified.
- **Port already in use**: something on your machine holds one of the ports listed under [Prerequisites](#prerequisites). Stop it, or for the source database only, change `SOURCE_MYSQL_PORT` in `.env`.
- **Memory**: containers restarting, or Elasticsearch exiting with code 137, means Docker is short of memory. Give Docker 8 GB.
- **OpenMetadata not up yet**: the first start runs database migrations; give it a few minutes. `docker compose ps` should show `execute_migrate_all` exited (0) and `openmetadata_server` healthy.
- **`openmetadata_mysql` unhealthy and restarting**: older checkouts bind-mounted its data from `openmetadata/docker-volume/db-data`, and InnoDB on a case-insensitive Windows mount can crash with an assertion in the purge thread. Pull the current `main`, which uses a named volume, and delete that folder.
- **OpenMetadata can't reach MySQL**: use `source-mysql:3306`, not `localhost`. Inside Docker, `localhost` is the ingestion container itself. Check name resolution with `docker exec openmetadata_ingestion getent hosts source-mysql`.
- **Git Bash on Windows turns `/tmp/...` into a Windows path**: prefix the `docker` commands with `MSYS_NO_PATHCONV=1`, or use PowerShell.
- **`seed.py: cannot connect to source MySQL`**: start the stack and wait for `source-mysql` to be healthy. Also check `SOURCE_MYSQL_PORT` in `.env`.
- **`table(s) ... not found`**: run the seeder once with `--init`.
- **Profiler row count lags `COUNT(*)`**: rows were inserted without `ANALYZE TABLE`. The seeder does this for you; after manual inserts, run it yourself, then re-run the profiler.

Problems inside the OpenMetadata UI (auto classification, the profiler, lineage) are covered in [docs/learning-path.md](docs/learning-path.md#troubleshooting).

## Pinned OpenMetadata version

`openmetadata/docker-compose.yml` is the official `docker-compose.yml` from the OpenMetadata **2.0.2** release (`2.0.2-release`), unmodified. It runs OpenMetadata server 2.0.2, Elasticsearch 9.3.0, and the ingestion image with Airflow 3.3.1.

- Source: https://github.com/open-metadata/OpenMetadata/releases/download/2.0.2-release/docker-compose.yml
- SHA-256: `2bc4af547288e7b5720d1596ceb8ddd242beed275200e31ea3b9b33634c5ad32`

To upgrade, replace the file with another release's `docker-compose.yml` as-is, then update this section.

## Phase 2 (planned)

An Oracle 21c XE source with legacy HR/payroll data, views and lineage, started with `docker compose --profile oracle up -d`. See [PLAN.md](PLAN.md).
