# openmetadata-dq-lab — Build Plan

Build brief for Claude Code. Implement everything below inside this repo.

## Goal

A local, testing-only OpenMetadata lab. Two source databases (MySQL and Oracle) receive fake data every day. Part of that data is deliberately bad. OpenMetadata catalogs both sources, profiles them, and runs data-quality tests that catch the bad rows.

The repo also serves as an onboarding resource for trainees: clone it, run one command, and learn data quality hands-on.

**Out of scope:** production hardening, SSO/auth, backups, HA, Kubernetes.

## Stack

| Component | Choice |
|---|---|
| Catalog | OpenMetadata. Use the latest stable release's official `docker-compose.yml`, pinned to that version and left unmodified |
| Source 1 | MySQL 8 (service `source-mysql`, host port **3307**) |
| Source 2 | Oracle 21c XE via `gvenzl/oracle-xe:21-slim-faststart` from Docker Hub (service `source-oracle`, port 1521, PDB `XEPDB1`) |
| Scheduler | OpenMetadata's bundled Airflow (ingestion container) |
| Seeder | Python 3, Faker, PyMySQL, python-oracledb (thin mode, so no Oracle Instant Client is needed) |
| Packaging | `requirements.txt` |
| License | MIT |

## Repo layout

```
openmetadata-dq-lab/
├── compose.yml                    # root: `include:` both files below
├── openmetadata/
│   └── docker-compose.yml         # official file, pinned version, unmodified
├── sources/
│   └── docker-compose.yml         # source-mysql + source-oracle
├── seed/
│   ├── seed.py                    # CLI entry point
│   ├── schema.py                  # DDL for both dialects
│   ├── generators.py              # clean + bad record generators
│   └── requirements.txt
├── pipelines/                     # reference YAML mirroring UI-configured pipelines
│   ├── mysql/{metadata,profiler,dq_tests}.yaml
│   └── oracle/{metadata,profiler,dq_tests}.yaml
├── .env.example
├── README.md
├── PLAN.md
└── LICENSE
```

## Compose

- Root `compose.yml` uses `include:` for `openmetadata/docker-compose.yml` and `sources/docker-compose.yml`. A single `docker compose up -d` starts everything.
- Source containers must join OpenMetadata's network (`app_net` in the official file) so the ingestion container can reach `source-mysql` and `source-oracle` by service name. Verify with `docker compose config`.
- OpenMetadata's internal metadata DB is also MySQL. Keep the source MySQL clearly separate: distinct service name, host port 3307, and its own volume.
- Credentials come from `.env` (commit `.env.example` only).
- Record the pinned OpenMetadata version in the README.
- Recommended Docker resources: 8 GB RAM and 4 vCPU. Document this in the README.

## Schema

The same three tables exist in both sources. The app user owns them: database `dqlab` in MySQL, app-user schema in Oracle.

**products**
- `product_id` (PK), `sku`, `name`, `category`, `unit_price`, `created_at`

**customers**
- `customer_id` (PK), `full_name`, `email`, `age`, `country`, `created_at`

**orders**
- `order_id` (PK), `customer_id`, `product_id`, `quantity`, `amount`, `status`, `order_date`

Deliberately **no** FK constraints, no UNIQUE on `email`/`sku`, and no NOT NULL except on PKs. This simulates a loosely constrained legacy source, so that bad rows land in the tables and it is the quality tests that catch them. Explain this choice in the README.

`seed.py --init` creates the tables idempotently for both dialects. Do not use image init scripts.

## Seed script

CLI, run by the host cron daily. Flags:

| Flag | Default | Purpose |
|---|---|---|
| `--init` | off | create tables if missing |
| `--target` | `all` | `mysql`, `oracle`, or `all` |
| `--customers` | 500 | new customers per run |
| `--orders` | 1500 | new orders per run |
| `--products` | 20 | new products per run (first run: 200) |
| `--bad-rate` | 0.10 | fraction of bad records |
| `--days` | 1 | backfill N days with back-dated `created_at`/`order_date` so trends appear immediately |
| `--seed` | none | RNG seed for reproducible runs |

Behavior:
- Append only. Never truncate.
- Each bad record carries one randomly chosen defect from its table's defect list below.
- Log a per-run summary: rows inserted per table and per defect type.
- Include an example crontab line in the README.

### Defects per table (and the OpenMetadata test that catches each)

| Table | Defect | OpenMetadata test |
|---|---|---|
| customers | null `full_name` | columnValuesToBeNotNull |
| customers | duplicate `email` | columnValuesToBeUnique |
| customers | malformed `email` | columnValuesToMatchRegex |
| customers | `age` outside 18–90 | columnValuesToBeBetween |
| customers | `country` not in allowed list | columnValuesToBeInSet |
| products | duplicate `sku` | columnValuesToBeUnique |
| products | `unit_price` ≤ 0 | columnValuesToBeBetween |
| products | null `category` | columnValuesToBeNotNull |
| orders | orphan `customer_id` | tableCustomSQLQuery (anti-join) |
| orders | orphan `product_id` | tableCustomSQLQuery (anti-join) |
| orders | `amount` ≤ 0 | columnValuesToBeBetween |
| orders | `quantity` ≤ 0 | columnValuesToBeBetween |
| orders | `status` not in {pending, shipped, delivered, cancelled} | columnValuesToBeInSet |
| orders | future `order_date` | tableCustomSQLQuery |

## OpenMetadata pipelines

The standard path: configure pipelines in the UI and deploy them to the bundled Airflow. Per source (MySQL, Oracle):

1. **Database service** connection: host `source-mysql:3306` / `source-oracle:1521`, service name `XEPDB1`.
2. **Metadata ingestion**, daily.
3. **Profiler**, daily, after metadata.
4. **Data quality test suite** containing every test in the table above, daily, after the profiler.

Suggested daily order (container time): seed at 01:00, metadata at 02:00, profiler at 02:30, tests at 03:00.

`pipelines/` holds YAML equivalents of these workflows as reference and fallback: runnable with `metadata ingest -c`, `metadata profile -c`, and `metadata test -c` from the ingestion container. Use env placeholders, never real secrets.

## README

Cover: purpose, architecture sketch, prerequisites, quickstart (`cp .env.example .env`, `docker compose up -d`, `python seed/seed.py --init --days 7`), UI walkthrough for adding services, pipelines, and tests, the cron line, the reasoning behind the schema design, and troubleshooting (Oracle startup time, memory, network).

## Acceptance criteria

1. `docker compose up -d` brings up all containers healthy. The UI is reachable at `localhost:8585` and Airflow at `localhost:8080`.
2. `seed.py --init --days 7` populates both sources. Running it again appends rows without errors.
3. Both sources appear in OpenMetadata with all three tables and their columns.
4. The profiler shows row counts and column stats that grow across runs.
5. The test suites show failures that match the injected defects. With `--bad-rate 0`, a fresh set of tables passes all tests.
6. A new user can go from clone to failing tests visible in the UI using only the README.
