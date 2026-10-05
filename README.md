# openmetadata-dq-lab

A local, testing-only lab for learning OpenMetadata's catalog and data-quality features hands-on. A seeder fills a source database with fake data on demand, a configurable share of it deliberately bad. OpenMetadata catalogs, profiles and tests that database, and the bad rows surface as failed tests you can triage.

| Phase | Source | Domain | Status |
|---|---|---|---|
| 1 | MySQL 8.4 | E-commerce: products, customers, orders | Ready |
| 2 | Oracle 21c XE | Legacy HR/payroll: views, lineage, legacy quirks | Planned |

Nothing is scheduled: seeding and every OpenMetadata pipeline run when you trigger them, so an instructor controls the pace. Out of scope: production hardening, auth/SSO, backups, HA, Kubernetes.

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

- `compose.yml` includes both compose files. `openmetadata/docker-compose.yml` is the official release file, pinned and never edited (see [Pinned OpenMetadata version](#pinned-openmetadata-version)).
- `source-mysql` is separate from OpenMetadata's internal MySQL: its own service, host port (3307) and volume. It joins OpenMetadata's network, so OpenMetadata reaches it as `source-mysql:3306`.
- `seed/seed.py` runs on your machine and appends data through `127.0.0.1:3307`.
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

5. Work through the [learning path](#learning-path).

## Class flow

1. Seed a clean baseline with `--init --bad-rate 0 --days 7`, then catalog, profile and test it: every test is green.
2. Seed "Monday's batch" with `python seed/seed.py --bad-rate 0.15`, re-run the profiler and the tests, and triage the red flags.

The seeder prints what it injected, and which test should catch each defect, so trainees can check their triage against it.

## Learning path

### 1. Seed a clean baseline

`python seed/seed.py --init --bad-rate 0 --days 7`. The tables must exist before OpenMetadata can ingest them.

### 2. Add the MySQL service and test the connection

Settings > Services > Databases > Add New Service > MySQL. This opens a three-step wizard: Select Service Type, Connect, What to Ingest.

| Field (Connect step) | Value |
|---|---|
| Service name | `dqlab_mysql`. The YAML files and test names assume this name. |
| Username / Password | `SOURCE_MYSQL_USER` / `SOURCE_MYSQL_PASSWORD` from `.env`. The password is under Authentication > Basic Auth. |
| Host and Port | `source-mysql:3306`. OpenMetadata runs inside Docker, so not `localhost:3307`. |
| Database Schema | `dqlab` (under Scope & Options). Leave Database Name and Query History Table empty. |

Click Test Connection. Every step should pass except GetQueries, which warns that the user can't read `mysql.general_log`. That's expected: query history feeds usage and lineage, which this lab doesn't use. A yellow "Test connection partially successful" banner appears, and you can still continue.

There is no Save button. Click Next: What to Ingest, keep the defaults (scan everything, system schemas excluded) and click **Create & Deploy**.

### 3. Run metadata ingestion

Create & Deploy creates one agent, **Metadata**, on the service's Agents tab, on a weekly schedule. Edit it (`⋮` > Edit) and set the schedule to On Demand, so it runs only when you click Run. Then click Run and wait for it to succeed. You add the other agents yourself in items 4 and 6.

Then explore `dqlab_mysql > default > dqlab`: three tables, their columns and types. Click Run on the Metadata agent any time you want to re-ingest.

### 4. Run auto classification for sample data

On the service's Agents tab, add an AutoClassification agent. Turn on Store Sample Data, turn off Enable Auto Classification, and set the schedule to On Demand. Save, then click Run. Each table gets a Sample Data tab with 50 rows (the Row Limit dropdown above it is only a display limit). In OpenMetadata 2.x this is the only pipeline that stores table sample data.

Enable Auto Classification (PII tagging) stays off in this lab. It downloads a spaCy language model from GitHub the first time it runs, and networks that inspect TLS block that download. On an open network, you can turn it on to get suggested PII tags on columns such as `email` and `full_name`.

### 5. Enrich the catalog

Add descriptions to tables and columns, set an owner, apply a tag or two, and create a glossary term (for example "Order", linked to `orders`).

### 6. Run the profiler

On the service's Agents tab, add a Profiler agent. Leave the filter patterns empty so it profiles every table, and set the schedule to On Demand. Save and click Run. On each table, Data Observability > Table Profile shows the row count, which matches the seeder's `total` column. Column Profile shows nulls, distinct values and min/max per column.

### 7. Create the tests and run them: everything green

Create the 13 tests in [Tests and the defects they catch](#tests-and-the-defects-they-catch). For each one, open the table, go to Data Observability, add a test case, and give it exactly the name, column, type and parameters in the table. Turn on Compute Row Count for each.

Then go to Data Quality > Test Suites and create a Bundle Suite named `dqlab_mysql_suite`. A Bundle Suite is OpenMetadata's name for a logical test suite, and it can span tables. Add all 13 test cases, add a pipeline with an On Demand schedule, and run it. All 13 tests pass.

Shortcut: [run the three `dq_tests_*.yaml` files](#pipelines-from-yaml) to create the test cases (this needs the ingestion bot's token in `.env`), then build the Bundle Suite in the UI. The test names match, so nothing is duplicated.

### 8. Seed a bad batch and triage

```sh
python seed/seed.py --bad-rate 0.15
```

Re-run the Profiler agent (row counts grow) and the Bundle Suite pipeline. Tests go red, and each failed test opens an incident in the Incident Manager: acknowledge, assign and resolve them there.

Compare every red test with the seeder's summary:
- A defect type with 0 rows leaves its test green. The products table only gets about 20 new rows per run, so it may not see every defect.
- Failed-row counts match the summary. The exception is uniqueness tests, which count both copies of each duplicate.

## Tests and the defects they catch

| Test name | Column | Test type (UI) | Parameters | Catches |
|---|---|---|---|---|
| `customers_full_name_not_null` | customers.full_name | Column Values To Be Not Null | | null `full_name` |
| `customers_email_unique` | customers.email | Column Values To Be Unique | | duplicate `email` |
| `customers_email_format` | customers.email | Column Values To Match Regex Pattern | RegEx Pattern: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$` | malformed `email` |
| `customers_age_between_18_and_90` | customers.age | Column Values To Be Between | Min 18, Max 90 | `age` outside 18–90 |
| `customers_country_allowed` | customers.country | Column Values To Be In Set | Allowed Values: `SA` `AE` `KW` `EG` `QA` `BH` `OM` `JO` `GB` `US`; Match enum: on | `country` not in the list |
| `products_sku_unique` | products.sku | Column Values To Be Unique | | duplicate `sku` |
| `products_unit_price_min_1` | products.unit_price | Column Values To Be Between | Min 1 | `unit_price` ≤ 0 |
| `products_category_not_null` | products.category | Column Values To Be Not Null | | null `category` |
| `orders_no_orphans` | orders (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `customer_id` or `product_id` |
| `orders_amount_min_1` | orders.amount | Column Values To Be Between | Min 1 | `amount` ≤ 0 |
| `orders_quantity_min_1` | orders.quantity | Column Values To Be Between | Min 1 | `quantity` ≤ 0 |
| `orders_status_allowed` | orders.status | Column Values To Be In Set | Allowed Values: `pending` `shipped` `delivered` `cancelled`; Match enum: on | `status` not in the set |
| `orders_no_future_dates` | orders (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | future `order_date` |

`orders_no_orphans` SQL Expression:

```sql
SELECT o.order_id, o.customer_id, o.product_id
FROM dqlab.orders o
LEFT JOIN dqlab.customers c ON c.customer_id = o.customer_id
LEFT JOIN dqlab.products p ON p.product_id = o.product_id
WHERE c.customer_id IS NULL OR p.product_id IS NULL
```

`orders_no_future_dates` SQL Expression:

```sql
SELECT order_id, order_date FROM dqlab.orders WHERE order_date > NOW()
```

### Reading the results

- **Match enum matters.** Without it, Column Values To Be In Set passes as soon as one value is allowed. With it, every row must be allowed.
- **Uniqueness counts both copies.** One injected duplicate makes two rows non-unique, so expect twice the seeder's duplicate count.
- **Bounds are inclusive whole numbers.** "Price ≤ 0 is bad" becomes Min 1. The lab never prices anything between 0 and 1.00.
- **MySQL compares text case-insensitively.** Under the default collation, `'PENDING' IN ('pending')` is true, so a case-only typo would slip past the set tests. The seeder's bad values differ by more than case (`canceled`, `UK`, `KSA`), and that blind spot is worth a discussion in class.
- **"Future" is relative to when the test runs.** Bad rows are dated 60 days to 2 years ahead.
- **Row counts come from MySQL's statistics.** OpenMetadata reads MySQL row counts from `information_schema.TABLES`, an InnoDB statistic. The seeder runs `ANALYZE TABLE` after every batch, and `source-mysql` samples enough pages that the count is exact. If you insert rows by hand, run `ANALYZE TABLE` before profiling.

## Why the sources have no constraints

The source tables have primary keys and nothing else: no foreign keys, `UNIQUE` or `NOT NULL`. In a well-guarded database, most of these defects could never be written. Real sources, especially legacy ones, are often looser than their documentation claims. Here the bad rows land, and it's the quality tests that have to catch them. That's the point of the lab.

## Seeder reference

`seed/seed.py` appends to the source database; it never truncates or updates.

| Flag | Default | Purpose |
|---|---|---|
| `--target` | `mysql` | `mysql`, `oracle` or `all` (Oracle arrives in Phase 2) |
| `--init` | off | Create the tables first; safe to repeat |
| `--customers` | 500 | New customers per run. Orders are about 3× this. Products get 200 rows on the first run, then 15–25 per run. |
| `--employees` | 100 | Phase 2 driver: new employees per run |
| `--bad-rate` | 0.10 | Share of each table's new rows that are bad |
| `--days` | 1 | Spread this run's rows over the last N days |
| `--seed` | random | RNG seed. The same seed on the same starting data gives the same batch. |

- Each bad row gets exactly one defect, picked at random from its table's list, and each table gets `round(rows × bad-rate)` bad rows.
- Timestamps come from the MySQL server's clock, so your machine's time zone doesn't matter.
- Clean rows stay clean across runs. Emails and SKUs embed the row id, and duplicates only copy values from rows with no other defect.
- Every run prints rows inserted per table, bad rows per defect type, and the test that should catch each defect.

## Pipelines from YAML

`pipelines/mysql/` mirrors the UI pipelines, for reference or when the UI isn't an option. The files contain `${...}` placeholders only; values come from your `.env`. To run them you need the ingestion bot's token: in OpenMetadata go to Settings > Bots > ingestion-bot, copy the token, and set `DQLAB_INGESTION_BOT_JWT` in `.env`.

Copy the files into the ingestion container (repeat after any edit), then run them there:

```sh
docker cp pipelines/. openmetadata_ingestion:/tmp/dqlab-pipelines

docker exec --env-file .env openmetadata_ingestion metadata ingest   -c /tmp/dqlab-pipelines/mysql/metadata.yaml
docker exec --env-file .env openmetadata_ingestion metadata classify -c /tmp/dqlab-pipelines/mysql/auto_classification.yaml
docker exec --env-file .env openmetadata_ingestion metadata profile  -c /tmp/dqlab-pipelines/mysql/profiler.yaml
docker exec --env-file .env openmetadata_ingestion metadata test     -c /tmp/dqlab-pipelines/mysql/dq_tests_customers.yaml
docker exec --env-file .env openmetadata_ingestion metadata test     -c /tmp/dqlab-pipelines/mysql/dq_tests_products.yaml
docker exec --env-file .env openmetadata_ingestion metadata test     -c /tmp/dqlab-pipelines/mysql/dq_tests_orders.yaml
```

- The metadata file creates the `dqlab_mysql` service if it doesn't exist yet.
- Each test file creates its table's missing test cases, then runs every test on that table. YAML can only create test cases one table at a time. The Bundle Suite that groups all 13 tests is created in the UI.

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
rm -rf openmetadata/docker-volume    # PowerShell: Remove-Item -Recurse -Force openmetadata/docker-volume
```

`down -v` removes the named volumes: source data, Elasticsearch and Airflow. OpenMetadata's own MySQL data is a bind mount under `openmetadata/docker-volume/`, so delete that folder too, or OpenMetadata will come back with its old catalog.

## Troubleshooting

- **`required variable SOURCE_MYSQL_ROOT_PASSWORD is missing a value`**: create `.env` from `.env.example`, in the repo root.
- **`the attribute 'version' is obsolete`**: a warning about the official OpenMetadata compose file. It's harmless and the file stays unmodified.
- **Port already in use**: something on your machine holds one of the ports listed under [Prerequisites](#prerequisites). Stop it, or for the source database only, change `SOURCE_MYSQL_PORT` in `.env`.
- **Memory**: containers restarting, or Elasticsearch exiting with code 137, means Docker is short of memory. Give Docker 8 GB.
- **OpenMetadata not up yet**: the first start runs database migrations; give it a few minutes. `docker compose ps` should show `execute_migrate_all` exited (0) and `openmetadata_server` healthy.
- **OpenMetadata can't reach MySQL**: use `source-mysql:3306`, not `localhost`. Inside Docker, `localhost` is the ingestion container itself. Check name resolution with `docker exec openmetadata_ingestion getent hosts source-mysql`.
- **Auto classification fails with `CERTIFICATE_VERIFY_FAILED` for raw.githubusercontent.com**: this happens when Enable Auto Classification (PII tagging) is on. It downloads a spaCy language model (`en_core_web_md`) from GitHub the first time it runs, and networks that inspect TLS (corporate proxies) break that download. Turn it back off; sample data is still stored.
- **Profiler run succeeds but there are no profiles ("Processed records: 0, Filtered: 3")**: the Profiler agent has a classification filter (for example `Tier1`/`Tier2`) that none of the lab's tables match. Delete the filter entries, as described in the learning path, item 6.
- **Lineage agent shows Failed**: expected if you added one. It needs query history (`mysql.general_log`), which the lab's user can't read. The lab doesn't use lineage, so delete it.
- **Git Bash on Windows turns `/tmp/...` into a Windows path**: prefix the `docker` commands with `MSYS_NO_PATHCONV=1`, or use PowerShell.
- **`seed.py: cannot connect to source MySQL`**: start the stack and wait for `source-mysql` to be healthy. Also check `SOURCE_MYSQL_PORT` in `.env`.
- **`table(s) ... not found`**: run the seeder once with `--init`.
- **Profiler row count lags `COUNT(*)`**: rows were inserted without `ANALYZE TABLE`. The seeder does this for you; after manual inserts, run it yourself, then re-run the profiler.

## Pinned OpenMetadata version

`openmetadata/docker-compose.yml` is the official `docker-compose.yml` from the OpenMetadata **2.0.2** release (`2.0.2-release`), unmodified. It runs OpenMetadata server 2.0.2, Elasticsearch 9.3.0, and the ingestion image with Airflow 3.3.1.

- Source: https://github.com/open-metadata/OpenMetadata/releases/download/2.0.2-release/docker-compose.yml
- SHA-256: `2bc4af547288e7b5720d1596ceb8ddd242beed275200e31ea3b9b33634c5ad32`

To upgrade, replace the file with another release's `docker-compose.yml` as-is, then update this section.

## Phase 2 (planned)

An Oracle 21c XE source with legacy HR/payroll data, views and lineage, started with `docker compose --profile oracle up -d`. See [PLAN.md](PLAN.md).
