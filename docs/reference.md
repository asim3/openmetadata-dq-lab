# Reference

Lookup material for the lab: the tests and the defects they catch, the seeder, the agents, and the map from OpenMetadata to the NDI domains. For the walkthrough, see the [learning path](learning-path.md).

## Tests and the defects they catch

| Test name | Column | Test type (UI) | Parameters | Catches | NDI dimension |
|---|---|---|---|---|---|
| `customers_full_name_not_null` | customers.full_name | Column Values To Be Not Null | | null `full_name` | Completeness |
| `customers_email_unique` | customers.email | Column Values To Be Unique | | duplicate `email` | Uniqueness |
| `customers_email_format` | customers.email | Column Values To Match Regex Pattern | RegEx Pattern: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$` | malformed `email` | Validity |
| `customers_age_between_18_and_90` | customers.age | Column Values To Be Between | Min 18, Max 90 | `age` outside 18–90 | Validity |
| `customers_country_allowed` | customers.country | Column Values To Be In Set | Allowed Values: `SA` `AE` `KW` `EG` `QA` `BH` `OM` `JO` `GB` `US`; Match enum: on | `country` not in the list | Validity |
| `products_sku_unique` | products.sku | Column Values To Be Unique | | duplicate `sku` | Uniqueness |
| `products_unit_price_min_1` | products.unit_price | Column Values To Be Between | Min 1 | `unit_price` ≤ 0 | Validity |
| `products_category_not_null` | products.category | Column Values To Be Not Null | | null `category` | Completeness |
| `orders_no_orphans` | orders (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `customer_id` or `product_id` | Consistency |
| `orders_amount_min_1` | orders.amount | Column Values To Be Between | Min 1 | `amount` ≤ 0 | Validity |
| `orders_quantity_min_1` | orders.quantity | Column Values To Be Between | Min 1 | `quantity` ≤ 0 | Validity |
| `orders_status_allowed` | orders.status | Column Values To Be In Set | Allowed Values: `pending` `shipped` `delivered` `cancelled`; Match enum: on | `status` not in the set | Validity |
| `orders_no_future_dates` | orders (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | future `order_date` | Validity |

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

### Quality dimensions

NDI expects every quality rule to name its dimension: completeness, uniqueness, timeliness, validity, accuracy or consistency. The last column gives each test's dimension. OpenMetadata's own label differs in two places: it calls a range check (Between) *Accuracy*, and it leaves Custom SQL Query without a dimension. A range check is a validity check in NDI's terms (values must lie in the permitted range), and the SQL tests here compare data across tables or columns, so they're *Consistency*. Pick one reading and keep it.

**Timeliness has no test in the lab.** OpenMetadata 2.0.2 has no dedicated freshness test; Table Row Inserted Count To Be Between is the closest.

### Reading the results

- **Match enum matters.** Without it, Column Values To Be In Set passes as soon as one value is allowed. With it, every row must be allowed.
- **Uniqueness counts both copies.** One injected duplicate makes two rows non-unique, so expect twice the seeder's duplicate count.
- **Bounds are inclusive whole numbers.** "Price ≤ 0 is bad" becomes Min 1. The lab never prices anything between 0 and 1.00.
- **MySQL compares text case-insensitively.** Under the default collation, `'PENDING' IN ('pending')` is true, so a case-only typo would slip past the set tests. The seeder's bad values differ by more than case (`canceled`, `UK`, `KSA`), and that blind spot is worth a discussion in class.
- **"Future" is relative to when the test runs.** Bad rows are dated 60 days to 2 years ahead.
- **Row counts come from MySQL's statistics.** OpenMetadata reads MySQL row counts from `information_schema.TABLES`, an InnoDB statistic. The seeder runs `ANALYZE TABLE` after every batch, and `source-mysql` samples enough pages that the count is exact. If you insert rows by hand, run `ANALYZE TABLE` before profiling.

## Oracle tests and the defects they catch

Phase 2 uses the same ideas on the Oracle HR source. The 12 tests live in the Bundle Suite `dqlab_oracle_suite`. Column names in the test form are lowercase, as OpenMetadata shows them.

| Test name | Column | Test type (UI) | Parameters | Catches | NDI dimension |
|---|---|---|---|---|---|
| `employees_full_name_not_null` | EMPLOYEES.full_name | Column Values To Be Not Null | | null `FULL_NAME` | Completeness |
| `employees_staff_no_unique` | EMPLOYEES.staff_no | Column Values To Be Unique | | duplicate `STAFF_NO` | Uniqueness |
| `employees_hire_date_format` | EMPLOYEES.hire_date | Column Values To Match Regex Pattern | RegEx Pattern: `^[0-9]{4}-[0-9]{2}-[0-9]{2}$` | `HIRE_DATE` text not `YYYY-MM-DD` | Validity |
| `employees_status_allowed` | EMPLOYEES.status | Column Values To Be In Set | Allowed Values: `A` `T`; Match enum: on | `STATUS` not `A` or `T` | Validity |
| `employees_no_orphan_dept` | EMPLOYEES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `DEPT_ID` | Consistency |
| `employees_dept_name_matches_master` | EMPLOYEES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | `DEPT_NAME` drifted from `DEPARTMENTS` | Consistency |
| `job_history_end_after_start` | JOB_HISTORY (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | `END_DATE` before `START_DATE` | Consistency |
| `salaries_base_amount_between_1_and_100000` | SALARIES.base_amount | Column Values To Be Between | Min 1, Max 100000 | `BASE_AMOUNT` ≤ 0 or absurdly high | Validity |
| `salaries_currency_sar` | SALARIES.currency | Column Values To Be In Set | Allowed Values: `SAR`; Match enum: on | `CURRENCY` other than SAR | Validity |
| `salaries_no_orphan_emp` | SALARIES (table-level) | Custom SQL Query | SQL below; Strategy ROWS; Operator `<=`; Threshold 0 | orphan `EMP_ID` | Consistency |
| `allowances_type_allowed` | ALLOWANCES.alw_type | Column Values To Be In Set | Allowed Values: `HOUSING` `TRANSPORT` `OTHER`; Match enum: on | invalid `ALW_TYPE` | Validity |
| `allowances_amount_min_0` | ALLOWANCES.amount | Column Values To Be Between | Min 0 | negative `AMOUNT` | Validity |

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
| `--init` | off | Create the tables (and, on Oracle, the views) first; safe to repeat. On Oracle it also lets the lab user read the data dictionary, which needs `SOURCE_ORACLE_SYSTEM_PASSWORD` in `.env`. |
| `--customers` | 500 | New customers per run. Orders are about 3× this. Products get 200 rows on the first run, then 15–25 per run. |
| `--employees` | 100 | Oracle: new employees per run. Each gets 1–3 `JOB_HISTORY`, 1–2 `SALARIES` and 1–3 `ALLOWANCES` rows. `DEPARTMENTS` (12 rows) is seeded once. |
| `--bad-rate` | 0.10 | Share of each table's new rows that are bad |
| `--days` | 1 | Spread this run's rows over the last N days. Oracle has no load timestamp, so there it spreads the effective dates of each new employee's latest raise and allowances; hire dates are always 1–12 years back. |
| `--seed` | random | Random seed. Optional. The numbers of rows also depend on the time of day, so don't expect two runs to match. |

- Each bad row gets exactly one defect, picked at random from its table's list, and each table gets `round(rows × bad-rate)` bad rows.
- Timestamps and dates come from the database server's clock (MySQL or Oracle), so your machine's time zone doesn't matter.
- Clean rows stay clean across runs. Emails and SKUs embed the row id, and duplicates only copy values from rows with no other defect.
- Every run prints rows inserted per table, bad rows per defect type, and the test that should catch each defect.

`fix_defects.py` takes `--dry-run`, which counts the bad rows and changes nothing, and `--target mysql|oracle|all` (default `mysql`). Both scripts check that every targeted database is reachable before they change anything. On Oracle it also deletes the history, salary and allowance rows left without an employee when a bad employee row is removed.

## Agents and AutoPilot

An **agent** is OpenMetadata's name for an ingestion pipeline: a saved job that connects to a service and does one kind of work. Deploying an agent creates an Airflow DAG in the ingestion container, and running it triggers that DAG. The lab schedules nothing, so every agent runs On Demand, from the Run button.

| Agent | What it does in the lab | Settings that matter |
|---|---|---|
| Metadata | Catalogs tables and columns (and views, on Oracle). Run it first. | Oracle: schema filter `(?i)^dqlab$`, Include Views on |
| Auto Classification | Stores 50 sample rows per table. In 2.x it's the only agent that does. | Store Sample Data on; Enable Auto Classification (PII) off |
| Profiler | Row counts and column statistics | Oracle: same schema filter; Include Views on to profile the views. With it on, a view gets column statistics but no table row count; with it off (AutoPilot's setting) the views get no profile at all. The switch is under Advanced Config in the agent's form. |
| Lineage | Links each Oracle view to the tables it selects from. The edge keeps the view's SQL, with literals shown as `?`. | Oracle only: same schema filter |
| Bundle Suite pipeline | Runs the tests of a Bundle Suite. It runs existing test cases and doesn't create any. | |

Things that go wrong:

- **Oracle without the schema filter** tries to catalog all of `SYS`, because the lab user can read the data dictionary. Every Oracle agent needs the filter.
- **A test case created wrongly is reused**, not recreated, so it keeps failing until you delete it. On Oracle that usually means a column name that isn't lowercase.
- **Two agents of one type** appear when you add your own and AutoPilot adds its copy later.

### AutoPilot

AutoPilot is an OpenMetadata application that creates and runs agents for a new service, so a user doesn't have to add them one by one. In the UI, Create & Deploy in the add-service wizard starts it, and there is nothing to press.

- Within about two minutes it creates five agents (provider `automation`, weekly schedule, shown as "Only on sunday") and runs the first three in order: Metadata, then Lineage, then Usage. Look at the Agents tab before adding your own.
- **Profiler and Auto Classification are created but not run.** They show "No status" and wait for their Sunday slot (Metadata 00:00, Lineage and Usage 02:00, Profiler and Auto Classification 04:00), so each needs an edit and a click on Run. AutoPilot's workflow is recorded as failed once Lineage fails on MySQL. These two agents stayed idle in the lab even after Lineage and Usage were deleted, so run them yourself.
- Its defaults, as observed:

 | Agent | Defaults | Result in the lab |
 |---|---|---|
 | Metadata | Include Views and Include Tags on | works |
 | Lineage | query and view lineage on | MySQL: fails, `SELECT command denied ... mysql.general_log`. Oracle: succeeds and creates the view-to-table edges |
 | Usage | | MySQL: "succeeds", finds nothing. Oracle: succeeds with 1 warning (it reaches its limit of 1,000 query-log entries); the entries are mostly Oracle's internal queries and OpenMetadata's own scanning, so the usage it records is noise |
 | Profiler | classification filter `Tier1`, `Tier2`; Include Views off | profiles nothing |
 | Auto Classification | **PII tagging on**, **Store Sample Data off**, confidence 80 | PII needs a GitHub download that a TLS-inspecting network blocks; no sample data |

- Edit the last two as in the [learning path](learning-path.md#3-run-metadata-ingestion), and delete Usage. Delete Lineage on MySQL, where it fails; keep it on Oracle.
- **Creating a service through the API does not start it.** Only the agents you create exist.
- Don't click Trigger AutoPilot after you've deleted agents: it recreates them.

Checked through the API, and in the UI on a MySQL service: Create & Deploy, the agents appearing within about two minutes, the Lineage failure, and the manual runs of Auto Classification (3 assets, 50 sample rows per table) and the Profiler (63 assets; row counts 200, 500 and the seeded order count). On an Oracle service it was checked through the API and in the UI: the same five agents appear within about two minutes, Metadata, Lineage and Usage succeed, Profiler and Auto Classification wait for Sunday, and the schema filter set in the wizard is copied into Metadata, Lineage, Profiler and Auto Classification. The Usage warning is the 1,000-entry limit. The manual runs of Auto Classification (7 assets, sample data stored) and the Profiler (94 assets; row counts 12, 100, 187, 138 and 202, matching the seeded rows) also succeeded on Oracle, with the schema filter in place. With Include Views off, the two views had no column profiles; after switching it on and running again, `v_monthly_payroll` showed 94 values and `v_current_employees` 100 in `emp_id`, and neither view has a table row count.

## NDI evidence map

What OpenMetadata can show for each of the 42 maturity questions of the National Data Index (NDI), SDAIA's index of data management in government entities. The questions, levels and evidence names come from SDAIA's *National Data Index* document (v1.1, Appendices I and II) and its *Operational Excellence* handbook. Both are in this folder and on https://sdaia.gov.sa/en/Research/Pages/NationalDataIndex.aspx. Codes such as `MCM.5.1` are specification numbers from those documents.

### How the levels work

Each question is scored from Level 0 to Level 5, and the evidence is cumulative: a level needs the acceptance evidence of every level below it.

| Level | Name | What it means | Evidence in practice |
|---|---|---|---|
| 0 | Absence of Capabilities | No practices. | None. |
| 1 | Establishing | Basic practices, not standardised. | A report of what is done today. |
| 2 | Defined | Practices are developed and formalised. | An approved plan, policy or process. |
| 3 | Activated | Processes, scalable tools and early automation are in place. | The tool in use: records, logs and screenshots. |
| 4 | Managed | Centralised governance, with KPIs and metrics. | A monitoring report built on predefined KPIs. |
| 5 | Pioneer | Continuous improvement and innovation. | A continuous-improvement report: reviews, results and the improvements made. |

OpenMetadata mostly gives you the Level 3 evidence, the numbers for Level 4, and the before-and-after for Level 5. Levels 1 and 2 are documents.

**Yes** (6): OpenMetadata produces most of the evidence. **Partly** (14): it shows part, the rest is a document or decision. **No** (22): a policy, plan or process outside the tool. "Course" is the item in the [learning path](learning-path.md); `G` items are the governance items.

| Question | What it asks | OpenMetadata | What to show | Course |
|---|---|---|---|---|
| DG.MQ.1 | Data management and personal data protection strategy and plan, with KPIs | No | Nothing in the tool. | - |
| DG.MQ.2 | Policies, standards and guidelines for all domains | No | Nothing in the tool. | - |
| DG.MQ.3 | Roles of the data management organisation | Partly | Teams, owners, domains and Data Steward roles show who does what. The appointment decisions are paper. | G1 |
| DG.MQ.4 | Change management: awareness, communication, change control, capability | Partly | Announcements, tasks and the activity feed as communication evidence. | G5 |
| MCM.MQ.1 | Plan to integrate and manage metadata | Partly | A catalog export as the report of documented metadata; the metadata structure (fields, custom properties, tags, glossary; `MCM.4.3`); Insights coverage as the implementation report. The plan is a document. | 5, G2, G4, G6 |
| MCM.MQ.2 | Metadata management and data catalog tool | Yes | The tool and its version (Settings > About); services as the prioritised data sources (`MCM.1.2`); the tool in use (`MCM.5.1`); roles and policies for access (`MCM.2.1`, `MCM.2.2`); adoption and use, such as active users and page views (`MCM.3.2`, `MCM.6.1`); the audit log (`MCM.5.3`); the version report (`MCM.5.4`); scheduled agents as automated metadata capture (Level 5). The training plan is a document. | 2, 3, G1, G6 |
| MCM.MQ.3 | Formal metadata processes (prioritising, populating, access, quality issues) | Yes | Governance workflows and tasks, such as glossary approval and tag, tier and owner updates; notification alerts and change logs (`MCM.5.2`); announcements as communication to users; owners and domains as the stewardship coverage model (`MCM.4.1`); annotation and certification (`MCM.4.6`, `MCM.4.7`); coverage KPIs (`MCM.6.2`). The process descriptions are documents. | G1, G2, G4, G5, G6 |
| DQ.MQ.1 | Data quality plan | Partly | Owners and stewards on tests and suites show the assigned roles and resources. The plan and roadmap are documents. | 7 |
| DQ.MQ.2 | Practices to manage and improve data quality | Yes | Rules with owner, description, dimension and threshold (`DQ.2.1`); the Tier priority list (`DQ.1.1`); profiling and test runs as the initial and periodic assessment (`DQ.1.3`); the incident workflow with root cause and resolution status (`DQ.2.3`); OpenMetadata as the tool automating the issue workflow (`DQ.2.5`); issues resolved against reported, and thresholds monitored (`DQ.3.2`). SLAs (`DQ.2.4`) are a document. | 6, 7, 8, 9, 13, 14, G4 |
| DQ.MQ.3 | Monitor and report data quality status | Yes | Quality dashboard and test suites as scorecards (`DQ.2.2`); rules and results registered as catalog metadata (`DQ.4.3`); users report issues through tasks and incidents (`DQ.4.2`); incident log and remediation (`DQ.4.1`); trends over time (`DQ.3.1`). | 7, 8, 9 |
| DQ.MQ.4 | Quality standards, dataset definitions, publish to the National Data Catalog | Partly | Descriptions, glossary terms and rules give the list of definitions and standards. Uploading them to the National Data Catalog is manual. | 5, 7, G2 |
| DO.MQ.1 | Plan for data operations, storage and retention | No | Nothing in the tool. | - |
| DO.MQ.2 | Standard operating procedures for database operations | No | Nothing in the tool. | - |
| DO.MQ.3 | Business continuity: backup, disaster recovery | No | Nothing in the tool. | - |
| DCM.MQ.1 | Document and content management and digitisation plan | No | Nothing in the tool. | - |
| DCM.MQ.2 | Document and content policies: backup, retention, access approval | No | Nothing in the tool. | - |
| DCM.MQ.3 | A document and content management tool | No | Nothing in the tool. | - |
| DAM.MQ.1 | Plan to improve data architecture capabilities | No | Nothing in the tool. | - |
| DAM.MQ.2 | Architecture and modelling practices: data flows, data models | Partly | Lineage records data flows and supports impact analysis; table and column schemas as the physical model; the glossary linked to columns. Conceptual models and policy are documents. | 11, 12, G2 |
| DSI.MQ.1 | Data sharing and integration plan | Partly | The services as the inventory of systems and data stores; lineage; schemas. The plan is a document. | 2, 10, 11 |
| DSI.MQ.2 | Processes for sharing data inside and with other entities | Partly | A data contract records what a producer promises its consumers (owner, schema, quality tests), as input to an internal sharing agreement. The agreements and the requests themselves are not OpenMetadata. | G5 |
| DSI.MQ.3 | Data integration architecture across stores, systems and applications | Partly | Lineage as the source-to-target flow. Requirements, solution designs and test scripts are documents. | 11, 12 |
| DSI.MQ.4 | Controls and processes for sharing and transforming data | No | Nothing in the tool. | - |
| RMD.MQ.1 | Reference and master data plan | No | Nothing in the tool. | - |
| RMD.MQ.2 | Processes managing reference and master data from creation to archival | Partly | Tags identify and classify reference and master data; tasks and version history as a change log. The lifecycle process is a document. | G4 |
| RMD.MQ.3 | A data hub as the trusted source | No | OpenMetadata is a catalog, not a master data hub (matching, merging, golden records, synchronisation). | - |
| BIA.MQ.1 | Business intelligence and analytics plan | No | Nothing in the tool. | - |
| BIA.MQ.2 | BI use cases and an implementation plan | No | Nothing in the tool. | - |
| BIA.MQ.3 | Management and governance of BI processes | No | OpenMetadata can catalog dashboards and charts from a BI tool, but the lab has no BI source. | - |
| BIA.MQ.4 | BI tools, technologies and skills | No | As above. | - |
| DVR.MQ.1 | Plan to realise revenue and cost value from data | No | Nothing in the tool. | - |
| DVR.MQ.2 | Practices supporting data revenue generation | No | Nothing in the tool. | - |
| OD.MQ.1 | Plan to identify and publish open datasets | No | Nothing in the tool. | - |
| OD.MQ.2 | Process to identify open data | Partly | The `Public` tag and a filter give the candidate list; descriptions are the documented metadata. Value and risk assessments are documents. | G3 |
| OD.MQ.3 | Process to publish open datasets | No | Publishing happens on the national open data platform. | - |
| FOI.MQ.1 | Plan for freedom of information compliance | No | Nothing in the tool. | - |
| FOI.MQ.2 | Freedom of information processes | No | Nothing in the tool. | - |
| DC.MQ.1 | Data classification plan | Partly | The Tier priority list and the catalog inventory feed the plan. The plan and its status reports are documents. | G3, G4 |
| DC.MQ.2 | Data classification processes | Yes | The catalog as the dataset inventory, with owners (`DC.3.1`); the prioritised datasets (`DC.1.2`); classification tags by level; the data register of datasets, levels and review dates (`DC.5.1`); access roles; auto classification as the classification automation tool (Level 5). The policy, impact assessments and handling controls (`DC.2.1`, `DC.3.2`, `DC.3.3`) are documents. | 4, G3 |
| DC.MQ.3 | Review of classified datasets | Yes | Levels published as catalog metadata (`DC.3.5`); the review as tag change history and approval tasks (`DC.3.4`); percentage classified and reviewed as KPIs. | G3, G6 |
| PDP.MQ.1 | Initial personal data assessment and plan | Partly | Personal-data tags list the types of personal data you hold and where it is stored (`PDP.1.1`). The plan and training are documents. | G3 |
| PDP.MQ.2 | Privacy policies and processes: breach, consent, data subject rights, risk assessment | Partly | Personal-data tags and quality tests on those tables. Consent, rights, breach notification and risk assessments (`PDP.3.1` to `PDP.4.3`) are processes outside OpenMetadata. | G3 |

Domains: DG data governance, MCM data catalog and metadata, DQ data quality, DO data operations, DCM document and content management, DAM data architecture and modelling, DSI data sharing and interoperability, RMD reference and master data, BIA business intelligence and analytics, DVR data value realisation, OD open data, FOI freedom of information, DC data classification, PDP personal data protection.

### Not an OpenMetadata thing

The 22 questions marked No are plans, policies and operations. Agree them between departments; the tool only holds their results afterwards.

| Who usually owns it | Questions |
|---|---|
| Data governance office | DG.MQ.1, DG.MQ.2, DAM.MQ.1, RMD.MQ.1, DVR.MQ.1 and 2, OD.MQ.1, FOI.MQ.1 and 2 |
| IT and database operations | DO.MQ.1, 2 and 3, DSI.MQ.4 |
| Records and content management | DCM.MQ.1, 2 and 3 |
| Master data owners and IT | RMD.MQ.3 |
| Business intelligence team | BIA.MQ.1, 2, 3 and 4 |
| Open data publisher | OD.MQ.3 |

Two things stay manual even when the rest is done in OpenMetadata: uploading dataset definitions to the National Data Catalog, and publishing open datasets. Auto classification needs a network that allows its model download; the lab's doesn't.

### Operational excellence

The index's third part, operational excellence (OE), is scored from how an entity uses the national data platforms, in six domains: metadata and catalog, data quality, data operations, sharing and interoperability, reference and master data, and open data. The metrics are calculated on those platforms, not in OpenMetadata, and each is scaled from Unacceptable to Leader. Several reward habits you can practise here:

| OE metric (handbook) | What it measures | The habit in OpenMetadata |
|---|---|---|
| `MCM.OE.01` Systems cataloged | Share of critical systems whose technical metadata is fully scanned and uploaded | Every critical source is a service with a successful Metadata agent run |
| `MCM.OE.02` Business attributes defined and linked | Share of required business attributes defined and linked to technical columns | Glossary terms linked to columns (G2) |
| `MCM.OE.03` Reporting assets defined | Share of required KPIs and metrics documented | Metrics defined in the catalog (G2) |
| `MCM.OE.04`, `MCM.OE.05` Standards and link accuracy | Attributes linked to standard attribute classes; share of wrongly linked attributes | Reviewed glossary terms with an owner and reviewer (G2) |
| `DQ.OE.01` Data quality index | Per rule and attribute: clean records divided by records checked, rolled up with weights | The passed-rows percentage of each test result |
| `DQ.OE.02` Conformance to data standards | The same, against the standards published in the National Data Catalog | Tests that encode your standards (item 7) |

### KPI cards

From Level 4, expect to report your KPIs as cards. A card typically gives: name and code, owner, description, the objective it measures, formula, unit, baseline, target, how often it's measured, data source, how it's collected (manually or automatically), whether higher is better, the current value against the target, and a status. Add recommendations and keep the data behind each value.

OpenMetadata can supply the numbers for these:

| KPI | Question | Where the number comes from |
|---|---|---|
| Percentage of assets with a description | MCM.MQ.1, MCM.MQ.3 | Insights |
| Percentage of assets with an owner | MCM.MQ.3 | Insights |
| Active users, page views | MCM.MQ.2 | Insights (daily active users, most viewed) |
| Percentage of critical systems cataloged | MCM.MQ.2 | Services with a successful Metadata agent run |
| Percentage of business terms linked to columns | MCM.MQ.3 | Glossary |
| Quality rules deployed | DQ.MQ.3 | Number of test cases |
| Data quality index | DQ.MQ.3 | Passed-rows percentage of each test result |
| Quality issues reported against resolved | DQ.MQ.2 | Incident Manager |
| Time to resolve a quality issue | DQ.MQ.2 | Incident status history (timestamps) |
| Percentage of datasets classified | DC.MQ.2, DC.MQ.3 | Count of assets with a level tag against all assets |
| Percentage of classified datasets reviewed | DC.MQ.3 | Custom property `classificationReviewedOn` |
