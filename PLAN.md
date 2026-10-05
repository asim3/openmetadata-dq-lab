# openmetadata-dq-lab — Build Plan

Build brief for Claude Code. Work through the milestones in section 6 in order: Phase 1 must be complete and usable before Phase 2 starts.

## 1. Overview

A local, testing-only lab for learning OpenMetadata's catalog and data-quality features hands-on. Source databases receive fake data on demand, a configurable share of it deliberately bad. OpenMetadata profiles and tests the sources, and the bad rows surface as failed tests. The repo doubles as an onboarding resource for new participants.

| Phase | Source | Domain | Purpose |
|---|---|---|---|
| 1 | MySQL 8 | E-commerce, clean-ish | Learn the full catalog → profiler → tests loop on easy mode |
| 2 | Oracle 21c XE | Legacy HR/payroll, messy | Views, lineage, and legacy quirks |

Principles:
- **On demand.** Nothing is scheduled. Seeding and every OpenMetadata pipeline are triggered by hand, so an instructor controls the pace.
- **Standard OpenMetadata path.** Pipelines are configured in the UI and deployed to the bundled Airflow.
- **Loose sources.** No FK, UNIQUE, or NOT NULL constraints except primary keys, so bad rows land and it's the quality tests that catch them.
- **Phase 1 stands alone.** Nothing in Phase 1 needs Oracle running.

Out of scope: production hardening, auth/SSO, backups, HA, Kubernetes, scheduling.

## 2. Shared foundation

### Stack

| Component | Choice |
|---|---|
| Catalog | OpenMetadata: official `docker-compose.yml` from the latest stable release, pinned and unmodified |
| Pipeline runner | Bundled Airflow; pipelines deployed with no schedule, run via the UI "Run" button |
| Phase 1 source | MySQL 8: service `source-mysql`, host port 3307, database `dqlab` |
| Phase 2 source | `gvenzl/oracle-xe:21-slim-faststart` (Docker Hub): service `source-oracle`, port 1521, PDB `XEPDB1` |
| Seeder | Python 3, Faker, PyMySQL, python-oracledb (thin mode, no Instant Client) |
| Packaging | `requirements.txt` |
| License | MIT |

Prerequisites: Docker Compose v2.20+ (needed for `include:`), 8 GB RAM and 4 vCPU recommended (more headroom once Oracle runs).

### Repo layout

```
openmetadata-dq-lab/
├── compose.yml                    # root: include: both files below
├── openmetadata/
│   └── docker-compose.yml         # official, pinned, unmodified
├── sources/
│   └── docker-compose.yml         # source-mysql (default) + source-oracle (profile: oracle)
├── seed/
│   ├── seed.py                    # CLI entry point
│   ├── mysql_schema.py            # e-commerce DDL
│   ├── mysql_generators.py        # clean + bad records
│   ├── oracle_schema.py           # HR DDL + views
│   ├── oracle_generators.py       # clean + bad records + legacy quirks
│   └── requirements.txt
├── pipelines/                     # optional test-case YAML (dq_tests_<table>.yaml)
│   ├── mysql/                     # dq_tests_{customers,products,orders}.yaml
│   └── oracle/                    # one dq_tests_<table>.yaml per tested table
├── .env.example
├── README.md                      # developer setup
├── docs/                          # learning-path.md (participants), reference.md
├── CLAUDE.md                      # guidance for Claude Code
├── PLAN.md
└── LICENSE
```

### Compose

- Root `compose.yml` includes `openmetadata/docker-compose.yml` and `sources/docker-compose.yml`.
- `source-oracle` sits behind the compose profile `oracle`:
  - Phase 1: `docker compose up -d` starts OpenMetadata and MySQL only.
  - Phase 2: `docker compose --profile oracle up -d` adds Oracle.
- Source services must share OpenMetadata's network (`app_net` in the official file). Choose wiring that works with `include:` without editing the official file, and confirm `source-mysql` resolves from inside the ingestion container.
- Keep the source MySQL separate from OpenMetadata's internal MySQL: its own service name, host port, and volume.
- Credentials live in `.env`; commit only `.env.example`. Record the pinned OpenMetadata version in the README.

### Seed CLI

`seed/seed.py`, run by hand.

| Flag | Default | Purpose |
|---|---|---|
| `--target` | `mysql` | `mysql`, `oracle`, or `all` |
| `--init` | off | Create tables and views idempotently (no image init scripts) |
| `--customers` | 500 | Phase 1 driver: new customers per run |
| `--employees` | 100 | Phase 2 driver: new employees per run |
| `--bad-rate` | 0.10 | Share of records that are bad |
| `--days` | 1 | Spread the run across N back-dated days |
| `--seed` | none | RNG seed for reproducible runs |

- Append only; never truncate.
- Each bad record gets exactly one defect, picked at random from its table's list.
- Print a per-run summary: rows inserted per table and bad rows per defect type.
- If Oracle is targeted but not running, fail fast with a clear message.

Class flow (for the README): seed a clean baseline with `--init --bad-rate 0 --days 7` and run the tests (all green). Then seed "Monday's batch" with `--bad-rate 0.15`, re-run the profiler and tests, and triage the red flags.

### OpenMetadata pipelines (per source)

Configured in the UI, deployed to the bundled Airflow with no schedule:

1. Database service connection
2. Metadata ingestion
3. Auto classification with "Store Sample Data" on and "Enable Auto Classification" (PII tagging) off. In OpenMetadata 2.x this is the only pipeline that stores table sample data; PII tagging downloads a spaCy model from GitHub on first use, which TLS-inspecting networks block.
4. Profiler
5. A logical test suite containing every test listed for that source (the tests span several tables)

`pipelines/<source>/` holds only the test-case YAML, an optional shortcut run from the ingestion container with `metadata test -c`. (The service, Metadata, Profiler and other agent YAML was dropped once the whole path was verified through the API: the UI is the supported path.) Tests get one `dq_tests_<table>.yaml` per table: YAML can only create test cases in a single-table run, and a logical-suite run only executes tests that already exist. Test case names match the README, so tests created in the UI and from YAML don't duplicate. Env placeholders only; no secrets.

## 3. Phase 1 — MySQL e-commerce

### Schema (database `dqlab`)

| Table | Columns |
|---|---|
| `products` | `product_id` PK, `sku`, `name`, `category`, `unit_price`, `created_at` |
| `customers` | `customer_id` PK, `full_name`, `email`, `age`, `country`, `created_at` |
| `orders` | `order_id` PK, `customer_id`, `product_id`, `quantity`, `amount`, `status`, `order_date` |

Scaling: products get 200 rows on the first run, then about 20 per run. Orders are about 3× `--customers` and reference existing customers and products.

Connection from OpenMetadata: `source-mysql:3306`.

Row counts: OpenMetadata reads MySQL row counts from `information_schema.TABLES`, an InnoDB statistics estimate that MySQL 8 caches for up to 24 hours. The seeder runs `ANALYZE TABLE` after every run, and `source-mysql` starts with a high `innodb_stats_persistent_sample_pages`, so the profiler's row counts match `COUNT(*)` at lab scale.

### Defects and tests

| Table | Defect | OpenMetadata test |
|---|---|---|
| customers | null `full_name` | columnValuesToBeNotNull |
| customers | duplicate `email` | columnValuesToBeUnique |
| customers | malformed `email` | columnValuesToMatchRegex |
| customers | `age` outside 18–90 | columnValuesToBeBetween |
| customers | `country` not in the allowed list | columnValuesToBeInSet |
| products | duplicate `sku` | columnValuesToBeUnique |
| products | `unit_price` ≤ 0 | columnValuesToBeBetween |
| products | null `category` | columnValuesToBeNotNull |
| orders | orphan `customer_id` or `product_id` | tableCustomSQLQuery (anti-join) |
| orders | `amount` ≤ 0 or `quantity` ≤ 0 | columnValuesToBeBetween |
| orders | `status` not in {pending, shipped, delivered, cancelled} | columnValuesToBeInSet |
| orders | future `order_date` | tableCustomSQLQuery |

### Learning path

1. Seed a clean baseline: `seed.py --init --bad-rate 0 --days 7` (the tables must exist before ingestion).
2. Add the MySQL service and test the connection.
3. Run metadata ingestion; explore tables and columns.
4. Run auto classification (sample data only); explore the sample data.
5. Enrich the catalog: descriptions, owners, tags, and a glossary term or two.
6. Run the profiler and read the row counts and column stats.
7. Create the test suite and run it: everything green.
8. Seed a bad batch, re-run the profiler and tests, and triage the red flags and the incidents they raise.

### Acceptance

1. `docker compose up -d` starts OpenMetadata and MySQL only; UI at `localhost:8585`, Airflow at `localhost:8080`.
2. `seed.py --init --days 7` populates MySQL; re-running appends without errors.
3. All MySQL tables appear in OpenMetadata; profiler row counts grow across runs.
4. Fresh tables seeded with `--bad-rate 0` pass every test; after a bad batch, the failures match the injected defects.
5. A new user gets from clone to red flags using only the README.

## 4. Phase 2 — Oracle legacy HR

### Schema (app-user schema in `XEPDB1`)

Uppercase identifiers, Oracle-native types. The seeder assigns primary keys itself (`MAX + 1`), as Oracle XE needs no sequences here. Oracle stores `''` as NULL, so a "blank" `STATUS` is a single space.

`--days` on Oracle: the tables have no load timestamp, so it spreads the effective dates of each new employee's latest raise and allowances over the last N days. Hire dates are 1 to 12 years back.

| Table | Columns |
|---|---|
| `DEPARTMENTS` | `DEPT_ID` PK, `DEPT_NAME`, `COST_CENTER` |
| `EMPLOYEES` | `EMP_ID` PK, `STAFF_NO`, `FULL_NAME`, `DEPT_ID`, `DEPT_NAME`, `HIRE_DATE`, `JOB_TITLE`, `STATUS` |
| `JOB_HISTORY` | `JH_ID` PK, `EMP_ID`, `DEPT_ID`, `JOB_TITLE`, `START_DATE`, `END_DATE` |
| `SALARIES` | `SAL_ID` PK, `EMP_ID`, `BASE_AMOUNT`, `CURRENCY`, `PAY_GRADE`, `EFFECTIVE_DATE` |
| `ALLOWANCES` | `ALW_ID` PK, `EMP_ID`, `ALW_TYPE` (HOUSING, TRANSPORT, OTHER), `AMOUNT`, `EFFECTIVE_DATE` |

Scaling: `DEPARTMENTS` is seeded once (about 12 rows). Each new employee gets 1–3 `JOB_HISTORY`, 1–2 `SALARIES`, and 1–3 `ALLOWANCES` rows.

Connection from OpenMetadata: `source-oracle:1521`, service name `XEPDB1`, views included.

Found while building M5: OpenMetadata's Oracle connector reads `DBA_TABLES`, so `seed.py --init` grants the app user `SELECT ANY DICTIONARY` (using the SYSTEM password from `.env`). That exposes `SYS`, so every Oracle pipeline filters schemas with `(?i)^dqlab$`. OpenMetadata lowercases the schema, column and view names. View lineage is its own agent (Lineage), run after Metadata.

### Legacy quirks (exactly three)

1. **Dates as text.** `EMPLOYEES.HIRE_DATE` is `VARCHAR2`: mostly `YYYY-MM-DD`, mixed formats in bad rows.
2. **One-character status.** `EMPLOYEES.STATUS` is `CHAR(1)`: `A` active, `T` terminated; bad rows get lowercase, blank, or junk values.
3. **Drifted copy.** `EMPLOYEES.DEPT_NAME` duplicates `DEPARTMENTS.DEPT_NAME`; in bad rows the two disagree.

### Views

- `V_CURRENT_EMPLOYEES`: each employee joined to their latest `JOB_HISTORY` row.
- `V_MONTHLY_PAYROLL`: latest base salary plus allowances per employee, filtered on `STATUS = 'A'`. Terminated staff and rows with bad status values (`'a'`, blank) silently drop out, so view totals disagree with the raw tables. This is an intentional teaching point.

### Defects and tests

| Table | Defect | OpenMetadata test |
|---|---|---|
| EMPLOYEES | null `FULL_NAME` | columnValuesToBeNotNull |
| EMPLOYEES | duplicate `STAFF_NO` | columnValuesToBeUnique |
| EMPLOYEES | `HIRE_DATE` not `YYYY-MM-DD` | columnValuesToMatchRegex |
| EMPLOYEES | `STATUS` not in {A, T} | columnValuesToBeInSet |
| EMPLOYEES | orphan `DEPT_ID` | tableCustomSQLQuery (anti-join) |
| EMPLOYEES | `DEPT_NAME` differs from master | tableCustomSQLQuery (join and compare) |
| JOB_HISTORY | `END_DATE` before `START_DATE` | tableCustomSQLQuery |
| SALARIES | `BASE_AMOUNT` ≤ 0 or absurdly high | columnValuesToBeBetween |
| SALARIES | `CURRENCY` other than SAR | columnValuesToBeInSet |
| SALARIES | orphan `EMP_ID` | tableCustomSQLQuery (anti-join) |
| ALLOWANCES | invalid `ALW_TYPE` | columnValuesToBeInSet |
| ALLOWANCES | negative `AMOUNT` | columnValuesToBeBetween |

### Learning path

9. Start Oracle, seed it, and add the service with views included.
10. Explore view lineage from the views back to their base tables.
11. Profile a view against its base tables and explain why `V_MONTHLY_PAYROLL` disagrees.
12. Hunt the legacy quirks: text dates, bad status codes, drifted department names.

### Acceptance

6. `docker compose --profile oracle up -d` adds Oracle without disturbing Phase 1 data.
7. `seed.py --target oracle --init --days 7` creates the tables and views and populates them.
8. All Oracle tables and both views appear in OpenMetadata, with view-to-table lineage.
9. Oracle test failures match the injected defects and quirks.

## 5. Documentation

Split by audience:

- `README.md` (developer setup): purpose, architecture sketch, prerequisites, quickstart, resetting, infrastructure troubleshooting (Oracle startup time, memory, networking), the pinned version, and the Phase 2 add-on.
- `docs/learning-path.md` (participants): the class flow, the step-by-step learning path, and UI troubleshooting.
- `docs/reference.md`: the tests and the defects they catch, why the sources have no constraints, the seeder reference, and the YAML pipelines.
- `CLAUDE.md`: repo rules and conventions for Claude Code.

## 6. Build order

| Milestone | Scope | Done when |
|---|---|---|
| M1 | Repo skeleton, root and sources compose (MySQL only), `.env.example` | Acceptance 1 |
| M2 | Seeder core, MySQL schema and generators | Acceptance 2 |
| M3 | MySQL pipeline YAML, README Phase 1 | Acceptance 3–5; **checkpoint: Phase 1 usable** |
| M4 | Oracle service under the `oracle` profile, schema, views, generators | Acceptance 6–7 |
| M5 | Oracle pipeline YAML, README Phase 2 | Acceptance 8–9 |
