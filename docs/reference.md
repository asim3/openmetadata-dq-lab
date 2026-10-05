# Reference

Lookup material for the lab: the tests and the defects they catch, the seeder, the agents, and the optional test-case YAML. For the walkthrough, see the [learning path](learning-path.md).

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

## Oracle tests and the defects they catch

Phase 2 uses the same ideas on the Oracle HR source. The 12 tests live in the Bundle Suite `dqlab_oracle_suite`. Column names in the test form are lowercase, as OpenMetadata shows them.

| Test name | Column | Test type (UI) | Parameters | Catches |
|---|---|---|---|---|
| `employees_full_name_not_null` | EMPLOYEES.full_name | Column Values To Be Not Null | | null `FULL_NAME` |
| `employees_staff_no_unique` | EMPLOYEES.staff_no | Column Values To Be Unique | | duplicate `STAFF_NO` |
| `employees_hire_date_format` | EMPLOYEES.hire_date | Column Values To Match Regex Pattern | RegEx Pattern: `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` | `HIRE_DATE` text not `YYYY-MM-DD` |
| `employees_status_allowed` | EMPLOYEES.status | Column Values To Be In Set | Allowed Values: `A` `T`; Match enum: on | `STATUS` not `A` or `T` |
| `employees_no_orphan_dept` | EMPLOYEES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `DEPT_ID` |
| `employees_dept_name_matches_master` | EMPLOYEES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | `DEPT_NAME` drifted from `DEPARTMENTS` |
| `job_history_end_after_start` | JOB_HISTORY (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | `END_DATE` before `START_DATE` |
| `salaries_base_amount_between_1_and_100000` | SALARIES.base_amount | Column Values To Be Between | Min 1, Max 100000 | `BASE_AMOUNT` ≤ 0 or absurdly high |
| `salaries_currency_sar` | SALARIES.currency | Column Values To Be In Set | Allowed Values: `SAR`; Match enum: on | `CURRENCY` other than SAR |
| `salaries_no_orphan_emp` | SALARIES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `EMP_ID` |
| `allowances_type_allowed` | ALLOWANCES.alw_type | Column Values To Be In Set | Allowed Values: `HOUSING` `TRANSPORT` `OTHER`; Match enum: on | invalid `ALW_TYPE` |
| `allowances_amount_min_0` | ALLOWANCES.amount | Column Values To Be Between | Min 0 | negative `AMOUNT` |

SQL Expressions (the connection user owns the tables, so there's no schema prefix):

```sql
-- employees_no_orphan_dept
SELECT e.EMP_ID, e.DEPT_ID
FROM EMPLOYEES e
LEFT JOIN DEPARTMENTS d ON d.DEPT_ID = e.DEPT_ID
WHERE d.DEPT_ID IS NULL

-- employees_dept_name_matches_master
SELECT e.EMP_ID, e.DEPT_NAME, d.DEPT_NAME AS MASTER_NAME
FROM EMPLOYEES e
JOIN DEPARTMENTS d ON d.DEPT_ID = e.DEPT_ID
WHERE e.DEPT_NAME <> d.DEPT_NAME

-- job_history_end_after_start
SELECT JH_ID, EMP_ID, START_DATE, END_DATE
FROM JOB_HISTORY
WHERE END_DATE < START_DATE

-- salaries_no_orphan_emp
SELECT s.SAL_ID, s.EMP_ID
FROM SALARIES s
LEFT JOIN EMPLOYEES e ON e.EMP_ID = s.EMP_ID
WHERE e.EMP_ID IS NULL
```

### The three legacy quirks

1. **Dates as text.** `EMPLOYEES.HIRE_DATE` is `VARCHAR2`. Clean rows are `YYYY-MM-DD`; bad rows use other formats (`15/03/2019`, `15-Mar-2019`, `20190315`, `2019-3-5`). The profiler can't give min/max dates for text, and the regex test is the only guard.
2. **One-character status.** `EMPLOYEES.STATUS` is `CHAR(1)`: `A` active, `T` terminated. Bad rows hold `a`, `t`, a blank (a single space) or junk. Oracle compares text case-sensitively, so `a` really differs from `A`.
3. **Drifted copy.** `EMPLOYEES.DEPT_NAME` repeats `DEPARTMENTS.DEPT_NAME`. In bad rows they disagree.

### The views

- `V_CURRENT_EMPLOYEES`: each employee with their latest `JOB_HISTORY` row.
- `V_MONTHLY_PAYROLL`: the latest base salary plus allowances per employee, **only where `STATUS = 'A'`**. Terminated staff and rows with a bad status silently drop out, so the view has fewer rows than `EMPLOYEES` and its totals disagree with the raw tables. That's intentional.

### Reading the Oracle results

- **Oracle stores an empty string as NULL.** A "blank" status is therefore a single space, which is a value, not a NULL.
- **Uniqueness counts both copies**, as in MySQL: three injected duplicate `STAFF_NO` rows give six failed rows.
- **OpenMetadata lowercases some Oracle names.** The schema shows as `dqlab`, columns as `base_amount` and views as `v_monthly_payroll`; table names keep their capitals (`SALARIES`). A test case created with an uppercase column name fails with a `StopIteration` error, and it keeps failing until you delete the test case and create it again.
- **Oracle needs the schema filter `(?i)^dqlab$`.** The lab user can read Oracle's data dictionary (OpenMetadata requires it), which also exposes the thousands of system tables in `SYS`. Without a filter, ingestion tries to catalog all of them.
- **`END_DATE` is empty for a current job.** That's fine: the test only flags an end before a start.

## Why the sources have no constraints

The source tables have primary keys and nothing else: no foreign keys, `UNIQUE` or `NOT NULL`. In a well-guarded database, most of these defects could never be written. Real sources, especially legacy ones, are often looser than their documentation claims. Here the bad rows land, and it's the quality tests that have to catch them. That's the point of the lab.

## Seeder reference

`seed/seed.py` appends to the source database; it never truncates or updates. `seed/fix_defects.py` is its counterpart: it deletes the bad rows ([learning path, item 9](learning-path.md#9-investigate-fix-and-resolve)).

| Flag | Default | Purpose |
|---|---|---|
| `--target` | `mysql` | `mysql`, `oracle` or `all` |
| `--init` | off | Create the tables first; safe to repeat |
| `--customers` | 500 | New customers per run. Orders are about 3× this. Products get 200 rows on the first run, then 15–25 per run. |
| `--employees` | 100 | Oracle: new employees per run. Each gets 1–3 `JOB_HISTORY`, 1–2 `SALARIES` and 1–3 `ALLOWANCES` rows. `DEPARTMENTS` (12 rows) is seeded once. |
| `--bad-rate` | 0.10 | Share of each table's new rows that are bad |
| `--days` | 1 | Spread this run's rows over the last N days. Oracle has no load timestamp, so there it spreads the effective dates of each new employee's latest raise and allowances; hire dates are always 1–12 years back. |
| `--seed` | random | RNG seed. The same seed on the same starting data gives the same batch. |

- Each bad row gets exactly one defect, picked at random from its table's list, and each table gets `round(rows × bad-rate)` bad rows.
- Timestamps come from the MySQL server's clock, so your machine's time zone doesn't matter.
- Clean rows stay clean across runs. Emails and SKUs embed the row id, and duplicates only copy values from rows with no other defect.
- Every run prints rows inserted per table, bad rows per defect type, and the test that should catch each defect.

`fix_defects.py` takes `--dry-run`, which counts the bad rows and changes nothing, and `--target mysql|oracle|all` (default `mysql`). On Oracle it also deletes the history, salary and allowance rows left without an employee when a bad employee row is removed.

## Agents and AutoPilot

An **agent** is OpenMetadata's name for an ingestion pipeline: a saved job that connects to a service and does one kind of work. Deploying an agent creates an Airflow DAG in the ingestion container, and running it triggers that DAG. The lab schedules nothing, so every agent runs On Demand, from the Run button.

| Agent | What it does in the lab | Settings that matter |
|---|---|---|
| Metadata | Catalogs tables and columns (and views, on Oracle). Run it first. | Oracle: schema filter `(?i)^dqlab$`, Include Views on |
| Auto Classification | Stores 50 sample rows per table. In 2.x it's the only agent that does. | Store Sample Data on; Enable Auto Classification (PII) off |
| Profiler | Row counts and column statistics | Oracle: same schema filter; Include Views on to profile the views. A view gets column statistics but no table row count. |
| Lineage | Links each Oracle view to the tables it selects from. The edge keeps the view's SQL, with literals shown as `?`. | Oracle only: same schema filter |
| Bundle Suite pipeline | Runs the tests of a Bundle Suite. It runs existing test cases and doesn't create any. | |

Things that go wrong:

- **Oracle without the schema filter** tries to catalog all of `SYS`, because the lab user can read the data dictionary. Every Oracle agent needs the filter.
- **A test case created wrongly is reused**, not recreated, so it keeps failing until you delete it. On Oracle that usually means a column name that isn't lowercase.
- **The ingestion bot's token changes** whenever OpenMetadata's data is wiped. The test YAML then fails with "The given token does not match the current bot's token" until you copy the new token into `.env`.
- **Two agents of one type** appear when you add your own and AutoPilot adds its copy later.

### AutoPilot

AutoPilot is an OpenMetadata application that creates and runs agents for a new service, so a user doesn't have to add them one by one. In the UI, Create & Deploy in the add-service wizard starts it, and there is nothing to press.

- It runs the Metadata agent at once, and creates Lineage, Usage, Profiler and Auto Classification agents (provider `automation`, weekly schedule). In a test that triggered it by hand through the API, all five existed within a few minutes. An earlier UI run saw some of them only after about an hour, so allow up to an hour and look at the Agents tab before adding your own.
- **Only Metadata runs.** The other agents wait for their weekly slot (Sunday: Metadata 00:00, Lineage and Usage 02:00, Profiler and Auto Classification 04:00), so each one needs a click on Run.
- Its defaults, as observed:

  | Agent | Defaults | Result in the lab |
  |---|---|---|
  | Metadata | Include Views and Include Tags on | works |
  | Lineage | query and view lineage on | fails: `SELECT command denied ... mysql.general_log` |
  | Usage | | "succeeds", finds nothing |
  | Profiler | classification filter `Tier1`, `Tier2`; Include Views off | profiles nothing |
  | Auto Classification | **PII tagging on**, **Store Sample Data off**, confidence 80 | PII needs a GitHub download that a TLS-inspecting network blocks; no sample data |

- Edit the last two as in the [learning path](learning-path.md#3-run-metadata-ingestion), and delete Lineage and Usage.
- **Creating a service through the API does not start it.** Only the agents you create exist.
- Don't click Trigger AutoPilot after you've deleted agents: it recreates them.

Checked by running the whole learning path through the API, and by triggering AutoPilot by hand on a MySQL test service. Not checked yet: AutoPilot started from the UI wizard (timing), and what it adds for an Oracle service.

## Test cases from YAML (optional)

Creating 25 test cases by hand takes a while, so `pipelines/mysql/` and `pipelines/oracle/` hold `dq_tests_*.yaml` files that create them for you. This is an optional shortcut: the lab doesn't use YAML for anything else. Add the service and run the Metadata agent in the UI first: the YAML only needs the tables to exist in OpenMetadata.

The files contain `${...}` placeholders only; values come from your `.env`. To run them you need the ingestion bot's token: in OpenMetadata go to Settings > Bots > ingestion-bot, copy the token, and set `DQLAB_INGESTION_BOT_JWT` in `.env`. The token changes if OpenMetadata's data is wiped, so copy it again then.

Copy the files into the ingestion container (repeat after any edit), then run them there:

```sh
docker cp pipelines/. openmetadata_ingestion:/tmp/dqlab-pipelines

# MySQL: 13 test cases
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/mysql/dq_tests_customers.yaml
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/mysql/dq_tests_products.yaml
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/mysql/dq_tests_orders.yaml

# Oracle: 12 test cases
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/oracle/dq_tests_employees.yaml
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/oracle/dq_tests_job_history.yaml
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/oracle/dq_tests_salaries.yaml
docker exec --env-file .env openmetadata_ingestion metadata test -c /tmp/dqlab-pipelines/oracle/dq_tests_allowances.yaml
```

- Each file creates its table's missing test cases, then runs every test on that table. YAML can only create test cases one table at a time, so there is one file per tested table. The Bundle Suite that groups them (`dqlab_mysql_suite`, `dqlab_oracle_suite`) is created in the UI.
- The test names match the tables above, so test cases created in the UI and from YAML don't duplicate. A test case that already exists is reused, not changed: delete a wrongly created one before re-running.
- `DEPARTMENTS` (Oracle) has no tests.
- The Oracle files use the table names as OpenMetadata shows them (`dqlab_oracle.default.dqlab.EMPLOYEES`) and lowercase column names.
