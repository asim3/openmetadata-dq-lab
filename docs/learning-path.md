# Learning path

Hands-on walkthrough for the lab. You learn what OpenMetadata does by using it: catalog data, describe and own it, classify it, trace it and test its quality. Each item ends with an **NDI evidence** line: which question of the National Data Index (NDI) maturity assessment the step gives you evidence for. `MCM.MQ.2` means the metadata and data catalog domain, maturity question 2 (the tool). The questions come from SDAIA's NDI document in this folder. The full map, including what OpenMetadata can't do for you, is in the [NDI evidence map](reference.md#ndi-evidence-map).

It assumes the lab is already running: your instructor or the [README](../README.md) has started the stack, and you can log in at http://localhost:8585 (`admin@open-metadata.org` / `admin`).

Run the `python` and `docker compose` commands from the repo root, with the virtual environment from the README quickstart active.

## Class flow

1. Seed a clean baseline, then catalog, profile and test it: every test is green.
2. Seed "Monday's batch" with bad rows, re-run the profiler and the tests, and triage the red flags.
3. Work the incidents: find the cause, fix the source rows, re-run the tests until they're green, and resolve the incidents (item 9).
4. Govern the catalog: teams, owners, a glossary, classification, trusted-data marks, announcements and a health check (items G1 to G7). It works on the same tables, so do it any time after item 5.
5. Optional, a second source: repeat the loop on Oracle's legacy HR data, with views and lineage (items 10 to 14).

The seeder prints what it injected, and which test should catch each defect, so you can check your triage against it.

## 1. Seed a clean baseline

```sh
python seed/seed.py --init --bad-rate 0 --days 7
```

The tables must exist before OpenMetadata can ingest them. **You should see** 200 products, 500 customers and roughly 1,400 to 1,600 orders in the seeder's summary. The order count differs a little on every run, so use your own numbers wherever this path quotes one.

## 2. Add the MySQL service and test the connection

Settings > Services > Databases > Add New Service > MySQL. This opens a three-step wizard: Select Service Type, Connect, What to Ingest.

| Field (Connect step) | Value |
|---|---|
| Service name | `dqlab_mysql`. The test names assume this name. |
| Username / Password | `SOURCE_MYSQL_USER` / `SOURCE_MYSQL_PASSWORD` from `.env`. The password is under Authentication > Basic Auth. |
| Host and Port | `source-mysql:3306`. OpenMetadata runs inside Docker, so not `localhost:3307`. |
| Database Schema | `dqlab` (under Scope & Options). Leave Database Name and Query History Table empty. |

Leave **Advanced Config** as it is: the scheme `mysql+pymysql`, no SSL files, no connection options and no sample data storage. Most connections never need it.

Click Test Connection. It runs a few checks and shows each one: the connection is established, the schemas are listed, and `dqlab` has 3 tables and 0 views. The last check fails with **Query history table not accessible** (`SELECT command denied ... for table 'general_log'`). That's expected: the lab's user can't read `mysql.general_log`, and query history only feeds usage and lineage, which this lab doesn't use for MySQL. Ignore the suggestion to grant `SELECT` on it. A yellow banner says "Test connection partially successful: Some steps had failures, we will only ingest partial metadata", and **Next: What to Ingest** stays available. The partial metadata is everything this lab uses.

There is no Save button. Click Next: What to Ingest. The page "What should we ingest?" confirms "Connected to source-mysql:3306" and has four sections, Databases, Schemas, Tables and Stored Procedures. Each is set to scan everything, and under Schemas the **Exclude system schemas** switch is on (it excludes `information_schema` and `performance_schema`). Leave all of it as it is and click **Create & Deploy**.

**NDI evidence:** `MCM.MQ.2` (the catalog tool in use, with its sources) and `DSI.MQ.1` (an inventory of systems and data stores).

## 3. Run metadata ingestion

Create & Deploy starts **AutoPilot**, an OpenMetadata feature that creates agents for a new service without you adding any. You don't press anything for this. Within about two minutes the service page shows them: the Insights tab has an Agents Status box, and the Agents tab lists the agents. AutoPilot's first pass runs the Metadata agent (it ingests the tables, and shows Success), then the Lineage agent (it fails on MySQL, shown as Failed with a Diagnose button) and the Usage agent (Success, with 0 queries). It also creates the Profiler and Auto Classification agents, but doesn't run them: they show "No status" and wait for Sunday. Look at the Agents tab before you add an agent of your own, because AutoPilot's copy would duplicate it. Then fix them all in one pass:

| Agent | What to do |
|---|---|
| Metadata | Keep it. Open its `⋮` menu > **Edit configuration**, click Next, choose On Demand and Submit. It has already run once. |
| Lineage | Delete it (`⋮` > **Delete agent**). It shows Failed with a Diagnose button; click the agent to see the error, the same `mysql.general_log` denial. The lab doesn't use lineage on MySQL. |
| Usage | Delete it. It succeeds but finds 0 queries. |
| AutoClassification | Keep it. Turn on Store Sample Data, turn off Enable Auto Classification (PII), set On Demand. Item 4. |
| Profiler | Keep it. Remove its classification filter (`Tier1`, `Tier2`), set On Demand. Item 6. |

The `⋮` menu of an agent has Pause, Re-deploy, Edit configuration and Delete agent; next to it are **Logs** and **Run**. The edit form has two steps: Configure Ingestion (the settings, then **Next**) and Schedule Interval (the **Schedule** and **On Demand** cards, then **Submit**).

Profiler and Auto Classification don't start by themselves, so click **Run** on each one after you've edited it. Run Auto Classification first (item 4), then the Profiler (item 6).

Don't click **Trigger AutoPilot** (top right of the service page; it's greyed out while AutoPilot runs and available afterwards): it recreates the agents you deleted, and Lineage would fail again. The blue "Agents deploying & ingesting metadata" banner can stay on "1 done · 0 running · 2 queued" until you've run the other agents, and then turns into a green "Deployment complete". Ignore it.

Then explore `dqlab_mysql > default > dqlab`: **you should see** three tables (`customers`, `orders`, `products`), their columns and types. Click Run on the Metadata agent any time you want to re-ingest.

**NDI evidence:** `MCM.MQ.2` and `MCM.MQ.3`: the Metadata agent's run history shows the catalog is kept up to date. In production you would put agents on a schedule: fully automated metadata capture is what Level 5 asks for. The lab runs them On Demand so you control the pace.

## 4. Run auto classification for sample data

Edit the AutoClassification agent that AutoPilot created (`⋮` > Edit configuration). Turn on Store Sample Data, turn off Enable Auto Classification, click Next, choose On Demand and Submit. Then click Run. If the agent isn't there yet, add one yourself on the Agents tab with the same settings, and delete AutoPilot's copy if it shows up later. **You should see** a Sample Data tab with 50 rows on each table (the Row Limit dropdown above it is only a display limit). In OpenMetadata 2.x this is the only pipeline that stores table sample data.

Enable Auto Classification (PII tagging) stays off in this lab. It downloads a spaCy language model from GitHub the first time it runs, and networks that inspect TLS block that download. On an open network, you can turn it on to get suggested PII tags on columns such as `email` and `full_name`.

**NDI evidence:** `DC.MQ.2`: stored sample data and auto classification support the inventory, and auto classification is the classification automation tool NDI names for Level 5, once PII tagging can run.

## 5. Enrich the catalog

Add descriptions to tables and columns, set an owner, apply a tag or two, and create a glossary term (for example "Order", linked to `orders`).

In Explore, open the tree under Databases (`mysql > dqlab_mysql > default > dqlab > Tables`) and click a table. The panel on the right has a pencil next to Description, Owners, Domains, Tier, Tags and Glossary Terms. Description opens an editor with a **Save** button. The table page has the same fields, and its Columns tab has an **Add** button under Tags and Glossary Terms for each column.

This is the quick version. Items G1 to G7 do it properly, with the evidence NDI asks for.

**NDI evidence:** `MCM.MQ.1` (what metadata you keep per asset: the metadata structure).

## 6. Run the profiler

Edit the Profiler agent that AutoPilot created (`⋮` > Edit configuration) and make two changes:

- **Remove the classification filter.** AutoPilot's profiler only profiles tables tagged `Tier1` or `Tier2`: in the agent's form, under **Filter Patterns**, the **Classifications** section is set to "Only specific classifications" with the rules "starts with Tier1" and "starts with Tier2". None of the lab's tables are tagged, so the run succeeds but profiles nothing ("Processed records: 0, Filtered: 3" in the logs). Switch it to "Scan all classifications".
- Click Next and set the schedule to On Demand, then Submit.

If the agent isn't there yet, add a Profiler agent yourself with those settings, and delete AutoPilot's copy if it shows up later. Click Run. On each table, Data Observability > Table Profile shows the row count, which matches the seeder's `total` column: **you should see** the same numbers the seeder printed: 200 for `products`, 500 for `customers`, and your order count for `orders`. Column Profile shows nulls, distinct values and min/max per column.

**NDI evidence:** `DQ.MQ.2`: profiling is the initial quality assessment, and OpenMetadata is the tool for profiling, rules and issue workflow.

## 7. Create the tests and run them: everything green

Create the 13 tests in [the test table](reference.md#tests-and-the-defects-they-catch). For each one, go to Observability > Data Quality > Test Cases and click **Add a Test case** (or use **Add tests** in a table's Asset Health box). Choose Table Level or Column Level, select the table (and the column), select the test type, and give it exactly the name and parameters in the table. For the Custom SQL Query tests, the test type is the **Custom Query** link next to Select Test Type. Names must start with a letter and use only letters, numbers and underscores. Turn on Compute Row Count for each.

Give each test a one-line description and an owner. NDI asks for a business description and an owner for every quality rule, and the Test type is its quality dimension in the [dimension column](reference.md#tests-and-the-defects-they-catch).

Then go to Data Quality > Test Suites and click **Add a Bundle Suite** (the page also lists Table Suites, which OpenMetadata creates for you, one per table). A Bundle Suite is OpenMetadata's name for a logical test suite, and it can span tables. Name it `dqlab_mysql_suite`, search and select all 13 test cases in the panel, and click **Create**. Then add a pipeline with an On Demand schedule, and run it. **You should see** all 13 tests pass.

**NDI evidence:** `DQ.MQ.2` and `DQ.MQ.3`: documented rules with an owner, a description, a quality dimension and a threshold, registered as catalog metadata with their results.

## 8. Seed a bad batch and triage

```sh
python seed/seed.py --bad-rate 0.15
```

Re-run the Profiler agent (row counts grow) and the Bundle Suite pipeline. Tests go red, and each failed test opens an incident in the Incident Manager.

Compare every red test with the seeder's summary:
- A defect type with 0 rows leaves its test green. The products table only gets about 20 new rows per run, so it may not see every defect.
- Failed-row counts match the summary. The exception is uniqueness tests, which count both copies of each duplicate.

[Reading the results](reference.md#reading-the-results) explains the other quirks you may run into.

**NDI evidence:** `DQ.MQ.3`: the failed tests are the issue log. The index's operational-excellence part also scores a *data quality index*: for each rule, the clean records divided by the records checked, as a percentage, averaged over the rules. Each test result shows exactly that as its passed-rows percentage, so you can work out your own.

## 9. Investigate, fix and resolve

Red tests are the start of a process, not the end of one. This is the workflow a data team follows, and the order matters:

1. **Triage.** Open each failed test (Data Quality > Test Cases, or the Incident Manager). Read the failed-row count and look at the failed rows. Compare with the seeder's summary: the counts should match, except that uniqueness tests count both copies of a duplicate.
2. **Own the incident.** Acknowledge the incident, assign it to someone and set a severity. From now on there is a named owner and a record of what happened. If the table has an owner, new incidents on it are assigned to that owner automatically.
3. **Find the root cause.** Ask where the bad rows came from before touching them. In a real company the cause is usually an upstream application bug, a faulty load job or a schema change, and the table's owner and lineage tell you who to talk to. In this lab the cause is the seeder's bad batch.
4. **Fix at the source.** Correct the rows, or move them out, in the source database, and fix whatever produced them. Cleaning up the symptom only brings the same defects back on the next load. In the lab, the owners' fix is a script that removes every bad row the seeder can inject:

 ```sh
 python seed/fix_defects.py --dry-run # count what would be fixed, change nothing
 python seed/fix_defects.py # fix everything
 ```

 It deletes the bad rows, and for a duplicate the row with the higher id. Deleting a customer or product also deletes the orders that pointed at it, so the orders table can shrink by more than the dry run's orphan count shows. It's safe to repeat, and it refreshes the table statistics so the profiler's row counts are current.

 To look at the rows and fix them yourself, open a MySQL prompt in the source container:

 ```sh
 docker compose exec source-mysql sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" dqlab'
 ```

 Then run statements such as these (lab examples; in production a fix goes through a ticket and a reviewed script, not an ad hoc statement). Type `exit` to leave.

 ```sql
 -- orders with a status that isn't allowed
 SELECT order_id, status FROM dqlab.orders
 WHERE status NOT IN ('pending', 'shipped', 'delivered', 'cancelled');

 -- orders with a non-positive amount or quantity
 DELETE FROM dqlab.orders WHERE amount <= 0 OR quantity <= 0;
 ```

5. **Re-run and resolve.** Re-run the Bundle Suite pipeline (re-run the Profiler too if you changed row counts) and confirm the tests are green again. Incidents don't close on their own when a test turns green, so resolve each one yourself, with a note on the cause and the fix. The history stays in OpenMetadata as an audit trail.

To start over instead of fixing rows one by one, ask your instructor to follow [Resetting](../README.md#resetting): that restores the clean baseline in the source database.

**NDI evidence:** `DQ.MQ.2` and `DQ.MQ.3`: the incident workflow with its root-cause notes. Count the incidents reported and resolved, and how long each took: those are the Level 4 quality KPIs.

## Govern the catalog: items G1 to G7

A catalog nobody owns, describes or classifies is just a list of tables. These items turn it into a governed one, and each leaves behind something you can show an assessor. Do them on the MySQL tables, and on Oracle's if you added it. The team, domain and classification names below are examples: use your own entity's.

Where OpenMetadata can't do the job, the item says so. Policies, plans and approvals between departments stay outside the tool; the [NDI evidence map](reference.md#ndi-evidence-map) lists which ones.

The sidebar and Settings names below were checked in the UI. The forms behind them were not, so if a field or button differs from what you see, tell your instructor.

### G1. Teams, owners and domains

1. Create a team: Settings > Team & User Management > Teams > Add Team. Name it `DataGovernanceOffice` (type Group) and add yourself.
2. Create two domains, a domain being the business area a table belongs to: Data Marketplace > Domains > Add Domain. Make `Commerce` for the MySQL tables and `HumanResources` for Oracle's.
3. On each table, set the **Owner** to your team and the **Domain** to the matching domain.
4. Give a person the built-in **Data Steward** role. They can then edit descriptions and tags without being an admin: that is how you hand someone a governance job without handing them the keys.

**You should see** the owner and domain in every table's header, and the team's page listing what it owns.

**NDI evidence:** `DG.MQ.3` and `MCM.MQ.3`: owners, domains and stewards show who looks after the data, and show the roles are in use. The appointment decisions and the organisation chart are paper, not something the tool holds.

### G2. A glossary of your own terms

Create a glossary (Govern > Glossary > Add Glossary) and add three or four terms the business uses, for example `Customer`, `Order`, `Employee`. Give each a definition, an owner and a reviewer. Link each term to what it describes: `Customer` to `customers`, `Employee` to `EMPLOYEES`. A new term goes through an approval step before it's accepted; approve one as the reviewer. Then define one **metric** (a reporting number the business relies on, such as `monthly_payroll_total`, with its description and how it's calculated), in Govern > Metrics.

**You should see** the term on the table, the table listed under the term, and the approved status.

**NDI evidence:** `MCM.MQ.1` and `MCM.MQ.3` (business metadata, and a workflow in the tool), `DQ.MQ.4` (data definitions), `DAM.MQ.2` (the model linked to the business glossary). The operational-excellence part counts the business terms defined and linked to technical columns, and the reporting assets (metrics) defined, in the national catalog: linking terms and defining metrics here is the same habit.

### G3. Classify the data

1. Create your own classification: Govern > Classification > Add Classification. Name it `Data Classification` and keep it mutually exclusive (one level per asset). Add four tags: `Top Secret`, `Secret`, `Restricted`, `Public`. These are the NDMO levels, from the highest impact to none.
2. Decide each level by impact, as NDI asks: if unauthorised disclosure would do high harm, the data is Top Secret; medium, Secret; low, Restricted; none, Public. Write your reason in the table's description.
3. Tag the personal-data columns by hand. Give each both a level and the built-in `PersonalData.Personal` tag: `customers.email`, `customers.full_name` and, on Oracle, `EMPLOYEES.full_name`. Tag the salary amounts (`SALARIES.base_amount`) `Restricted`. Tag `products` `Public`: it's catalog data with nothing personal in it.
4. Add a custom property `classificationReviewedOn` (type string or date, Settings > Custom Properties > Tables) and fill in today's date on each table you classified.
5. Find what you missed: in Explore, filter by your tag and open the untagged tables. Then change one level, and look at the table's history: who changed it, and when.

**You should see** the tags on the columns and tables, a filter that returns exactly what you tagged, and a version history showing the change.

Auto classification (item 4) is the tool NDI wants for the top level, but PII tagging is off in this lab because of the network. On an open network it suggests the PII tags and the level still needs a human's decision.

**NDI evidence:** `DC.MQ.2` (the catalog used as the inventory; datasets with owners; a register of levels and review dates), `DC.MQ.3` (levels published as catalog metadata; the review is the change history), `PDP.MQ.1` (what personal data you hold and where), `OD.MQ.2` (the `Public` filter is the candidate list). The classification plan, the impact assessment report and the handling controls are documents. Consent, data subject rights, breach notification within 72 hours and risk assessments (`PDP.MQ.2`) are processes outside OpenMetadata.

### G4. Mark what matters most

Not all data is equally important, and NDI asks you to say which is first.

- **Tier.** Set `Tier1` on `orders` and `customers`. It's your priority list.
- **Certification.** Set `Gold` on a table someone vouches for.
- **Kind of data.** Create a classification `Data Kind` with `Reference`, `Master` and `Transactional`, and tag the tables. `DEPARTMENTS` is reference data, `customers`, `products` and `EMPLOYEES` are master data, `orders` and `SALARIES` are transactional.
- **Retention.** Add a custom property `retentionPeriod` (string) and set it to `7 years` on one table. It records the rule; nothing deletes data.

Setting `Tier1` also matters to AutoPilot's Profiler agent, which only profiles `Tier1` and `Tier2` tables (item 6): do item 6 first, or remove that filter.

**You should see** the tier and certification in the table header and in search, and the kind of data on each table.

**NDI evidence:** `DQ.MQ.2` (the priority list of data elements), `MCM.MQ.3` (certification of metadata), `RMD.MQ.2` (identifying and classifying reference and master data). OpenMetadata is not a master data hub, so `RMD.MQ.3` stays a separate system.

### G5. Announce, ask, approve and be notified

- **Announce:** on `customers`, add an announcement ("Customers is now classified Restricted"). It shows on the table and in the activity feed.
- **Ask:** on a table with no description, request one, assigned to a person. It shows up as a task for them, and they accept or decline it.
- **Be notified:** create a notification (Settings > Notifications) for changes to tables, and send it to yourself or your team. Observability > Alerts is the sibling for test results and pipeline status.
- **Contract** (optional): on `customers`, create a data contract naming the owner, the schema and the quality tests that must pass. It's what a team promises anyone using its data.

**You should see** the announcement and the task in the activity feed, and the notification listed under Settings > Notifications.

**NDI evidence:** `DG.MQ.4` (communication reaches the people who use the data), `MCM.MQ.3` (logs and notifications of metadata changes; telling users about updates; workflows in the tool), `DSI.MQ.2` in part (a contract records what a team promises the people who use its data).

### G6. Check the catalog's health and use

Open Insights in the left menu. The Data Assets tab shows the total number of assets and the share with a description, an owner and a tier, and how each changes over time. The App Analytics tab shows who uses OpenMetadata and which assets are viewed most. After G1 to G5 the percentages go up: that's the measurable result of your work. If the charts are empty, run the Data Insights application once from Settings > Applications.

Then open **KPIs** in the left menu of that page and add a KPI (**Add KPI**), such as description coverage, with a target and an end date. NDI's Level 4 asks for KPIs defined in advance. The audit log of who logged in and changed what is available through the API (`/api/v1/audit/logs`); I haven't found a menu for it.

**You should see** description coverage, owner coverage, a tier breakdown, daily active users and most viewed assets.

**NDI evidence:** `MCM.MQ.2` (adoption and use: active users and page views; regular audits of use), `MCM.MQ.1` (how much metadata is filled in) and `DC.MQ.3` for the coverage numbers. Level 4 asks for monitoring reports built on predefined KPIs and Level 5 for continuous-improvement reports, so screenshot now and again after more work, and fill in a KPI card from the [reference](reference.md#kpi-cards).

### G7. Collect your evidence

Open the [NDI evidence map](reference.md#ndi-evidence-map). For every question marked Yes or Partly it names what to capture. Take a dated screenshot or export of each thing you did. The rows marked No aren't things OpenMetadata can do: the map says which team usually owns them.

## Phase 2: the Oracle legacy HR source

Items 10 to 14 repeat the loop on a messier source: Oracle, with views, lineage and legacy quirks. Your instructor starts Oracle first ([README: Phase 2](../README.md#phase-2-add-oracle)). The tests, quirks and views are listed in the [reference](reference.md#oracle-tests-and-the-defects-they-catch).

### 10. Add the Oracle service

```sh
python seed/seed.py --target oracle --init --bad-rate 0 --days 7
```

**You should see** 12 departments, 100 employees, roughly 200 job history, 150 salary and 200 allowance rows, and `V_MONTHLY_PAYROLL` with a few rows fewer than the 100 employees (the summary prints the exact numbers).

Then Settings > Services > Databases > Add New Service > Oracle. It is the same three-step wizard as item 2: Select Service Type, Connect, What to Ingest.

| Field (Connect step) | Value |
|---|---|
| Service name | `dqlab_oracle`. The test names assume this name. |
| Username | `SOURCE_ORACLE_USER` from `.env` |
| Oracle Connection Type | Click **Oracle Service Name**. The form opens on Database Schema, which is the wrong one. Then set Oracle Service Name to `XEPDB1`. |
| Host and Port | `source-oracle:1521`, not `localhost` |
| Password | Under Authentication: `SOURCE_ORACLE_PASSWORD` from `.env`. Don't use `SOURCE_ORACLE_SYSTEM_PASSWORD`: it looks similar, but the test fails with `ORA-01017: invalid username/password`. |

Leave **Scope & Options** and **Advanced Config** as they are. In Scope & Options, **Use DBA Tables** is on (the lab user's `SELECT ANY DICTIONARY` grant is what allows it) and **Preserve Identifier Case** is off (which is why OpenMetadata shows lowercase names). Don't change either.

Click Test Connection. It runs six checks (package access, list schemas, list tables, list views, materialized views, query history) and all of them should pass. A successful test unlocks the next step.

There is no Save button. Click **Next: What to Ingest** at the bottom of the page, and on that page set:

- **Schemas:** click **Only specific schemas**. Under "Include only schemas where the name...", open the operator list and pick **matches regex**, type `(?i)^dqlab$` in the box and click **Add**. A chip appears, the section header says "Including 1 rule", and the preview reads "Only schemas matching 1 include rule are in scope" and the equivalent regex is `includes += (?i)^dqlab$`. This is essential. The lab user can read Oracle's data dictionary, which lists many system schemas, and **Exclude system schemas** only removes four of them (`sys`, `ctxsys`, `dbsnmp`, `outln`). Without the include rule, ingestion tries to catalog the rest.
- **Databases, Tables, Stored Procedures:** leave them on scan all. The wizard has no Include Views setting: views are switched on in the agents, below.

Click **Create & Deploy**. As in item 3, AutoPilot adds five agents within about two minutes (open the service's Agents tab) and runs Metadata, Lineage and Usage. Unlike MySQL, all three succeed: Lineage finds the view-to-table edges, and Usage reads 1,000 query-log entries and ends with one warning (it hit its limit of 1,000), but they are mostly Oracle's own internal queries and OpenMetadata's own scanning, so the usage it adds to the lab tables (a "Usage: 29th pctile" figure in the table header, and entries in the Queries tab) is not real use. AutoPilot copies your schema filter into the Metadata, Lineage, Profiler and Auto Classification agents, so you don't need to add it again; the Usage agent has no filter. Give each agent you keep an On Demand schedule, and delete the Usage agent (the lab has no real query traffic to measure). [Agents and AutoPilot](reference.md#agents-and-autopilot) explains each agent. **You should see** five tables and two views under `dqlab_oracle > default > dqlab`, and a Sample Data tab with 50 rows on the big tables (`DEPARTMENTS` has all 12). OpenMetadata shows the view names in lowercase (`v_monthly_payroll`).

Then run auto classification and the profiler as in items 4 and 6, with the same schema filter. AutoPilot's Profiler has **Include Views** off, and then it skips the views entirely (no column statistics). Turn it on in the agent's form (`⋮` > Edit configuration): it is the switch at the bottom of the first step, under **Advanced Config** (below Metrics, above Compute Table Metrics). Item 12 needs the views profiled, so run the Profiler again after you change it.

### 11. Explore view lineage

Use the Lineage agent on the service's Agents tab (AutoPilot creates one; add one yourself if it isn't there), give it the same schema filter, and run it. Unlike MySQL, it works here. It reads each view's SQL and links the view to the tables it selects from. Open `v_current_employees` and `v_monthly_payroll` and click Lineage. The first reads `EMPLOYEES` and `JOB_HISTORY`; the second reads `EMPLOYEES`, `SALARIES` and `ALLOWANCES`.

**NDI evidence:** `DAM.MQ.2` and `DSI.MQ.3`: lineage records data flows from tables to views and supports impact analysis.

### 12. Explain why `V_MONTHLY_PAYROLL` disagrees

Compare the view with the table it reads. Open `EMPLOYEES` and then `v_monthly_payroll`, go to Column Profile and look at `emp_id`: the table has 100 values after the baseline, the view a few fewer. (A view's Table Profile shows no row count, so use a column's Values Count.)

To see why, open the lineage from item 11 and click the edge between a table and the view: it shows the view's SQL (literal values appear as `?`), which ends in `WHERE e.STATUS = ?`. The value is `'A'`, so terminated staff drop out, and so does any row with a bad status. The view isn't broken; it quietly answers a different question than the raw tables do, which is why a report's totals need checking against their sources.

**NDI evidence:** `DSI.MQ.3` (checking a shared view against its sources).

### 13. Test the baseline: everything green

Create the 12 tests in [the Oracle test table](reference.md#oracle-tests-and-the-defects-they-catch), using the lowercase column names the UI shows. Create a Bundle Suite named `dqlab_oracle_suite` with all 12 and an On Demand pipeline, and run it. On the clean baseline **you should see** all 12 green.

### 14. Hunt the legacy quirks, triage and fix

Seed a bad batch, then re-run the Profiler agent and the suite:

```sh
python seed/seed.py --target oracle --bad-rate 0.15
```

Tests go red and raise incidents, with failed-row counts matching the seeder's summary (uniqueness counts both copies). A defect type with 0 rows in the summary leaves its test green; with only 100 employees per run that can happen to the drifted-name defect, which is only one of six for `EMPLOYEES`. Look for the three quirks:

- **Text dates:** `HIRE_DATE` is a `VARCHAR2`. Its column profile has no date min/max; its Min and Max are string lengths, and a bad format makes them differ from 10. `employees_hire_date_format` lists the rows.
- **Status codes:** `STATUS` is `CHAR(1)`. Its Distinct Count in the column profile should be 2 (`A`, `T`) and is higher once bad codes (`a`, a blank, junk) arrive.
- **Drifted names:** `EMPLOYEES.DEPT_NAME` duplicates `DEPARTMENTS.DEPT_NAME`. The profile can't show this; only `employees_dept_name_matches_master` can, and its failed rows list the mismatches.

Work the incidents as in item 9. The owners' fix is:

```sh
python seed/fix_defects.py --target oracle --dry-run
python seed/fix_defects.py --target oracle
```

It deletes the bad rows (for a duplicate, the higher id), plus the history, salary and allowance rows left without an employee, so those tables shrink by more than the dry run shows. Re-run the profiler and the suite: all 12 are green. Incidents stay open until you resolve them.

**NDI evidence:** `DQ.MQ.2` and `DQ.MQ.3`, as in items 7 to 9.

## Troubleshooting

- **Auto classification fails with `CERTIFICATE_VERIFY_FAILED` for raw.githubusercontent.com**: this happens when Enable Auto Classification (PII tagging) is on. It downloads a spaCy language model (`en_core_web_md`) from GitHub the first time it runs, and networks that inspect TLS (corporate proxies) break that download. Turn it back off; sample data is still stored.
- **Profiler run succeeds but there are no profiles ("Processed records: 0, Filtered: 3")**: AutoPilot's Profiler agent has a classification filter limited to `Tier1`/`Tier2`, which none of the lab's tables match. Delete the filter entries, as described in item 6.
- **MySQL Lineage agent shows Failed**: expected. It needs query history (`mysql.general_log`), which the lab's user can't read. The lab doesn't use lineage on MySQL, so delete the Lineage and Usage agents there. (Oracle's Lineage agent works: it reads the views' SQL.)
- **Two Profiler or two AutoClassification agents**: you added your own and AutoPilot added its copy. Keep one of each, configured as in items 4 and 6, and delete the other.
- **Can't connect to MySQL from the service wizard**: use `source-mysql:3306`, not `localhost`.
- **Oracle connection test fails, or ingestion lists thousands of `sys` tables**: see the Oracle entries in the [README troubleshooting](../README.md#troubleshooting). Both come down to the dictionary grant (`seed.py --target oracle --init`) and the `(?i)^dqlab$` schema filter.
- **An Oracle test run fails with `StopIteration`**: the test's column name must be lowercase, as the UI shows it. Delete the test case and create it again.
- **Can't connect to Oracle from the service wizard**: use `source-oracle:1521`, not `localhost`.
