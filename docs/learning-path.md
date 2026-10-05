# Learning path

Hands-on walkthrough for the lab. It assumes the lab is already running: your instructor or the [README](../README.md) has started the stack, and you can log in at http://localhost:8585 (`admin@open-metadata.org` / `admin`).

Run the `python` and `docker compose` commands from the repo root, with the virtual environment from the README quickstart active.

## Class flow

1. Seed a clean baseline, then catalog, profile and test it: every test is green.
2. Seed "Monday's batch" with bad rows, re-run the profiler and the tests, and triage the red flags.
3. Work the incidents: find the cause, fix the source rows, re-run the tests until they're green, and resolve the incidents (item 9).

The seeder prints what it injected, and which test should catch each defect, so you can check your triage against it.

## 1. Seed a clean baseline

```sh
python seed/seed.py --init --bad-rate 0 --days 7
```

The tables must exist before OpenMetadata can ingest them.

## 2. Add the MySQL service and test the connection

Settings > Services > Databases > Add New Service > MySQL. This opens a three-step wizard: Select Service Type, Connect, What to Ingest.

| Field (Connect step) | Value |
|---|---|
| Service name | `dqlab_mysql`. The YAML files and test names assume this name. |
| Username / Password | `SOURCE_MYSQL_USER` / `SOURCE_MYSQL_PASSWORD` from `.env`. The password is under Authentication > Basic Auth. |
| Host and Port | `source-mysql:3306`. OpenMetadata runs inside Docker, so not `localhost:3307`. |
| Database Schema | `dqlab` (under Scope & Options). Leave Database Name and Query History Table empty. |

Click Test Connection. Every step should pass except GetQueries, which warns that the user can't read `mysql.general_log`. That's expected: query history feeds usage and lineage, which this lab doesn't use. A yellow "Test connection partially successful" banner appears, and you can still continue.

There is no Save button. Click Next: What to Ingest, keep the defaults (scan everything, system schemas excluded) and click **Create & Deploy**.

## 3. Run metadata ingestion

Create & Deploy starts **AutoPilot**, an OpenMetadata feature that creates agents for a new service and runs them without you adding any. You don't press anything for this. It runs the Metadata agent straight away. About an hour later it adds more agents, all on a weekly schedule. Expect these on the service's Agents tab:

| Agent | What to do |
|---|---|
| Metadata | Keep it. Edit it (`⋮` > Edit) and set the schedule to On Demand. It has already run once. |
| Lineage | Delete it. It fails (same `mysql.general_log` denial) and the lab doesn't use lineage. |
| Usage | Delete it. It finds 0 queries. |
| Profiler, AutoClassification | They appear about an hour later. Items 4 and 6 configure them. |

Don't click Trigger AutoPilot, if you see it: it recreates the agents you deleted. The blue "Agents deploying" banner can stay stuck on a count like "2 queued" after you edit the agents; ignore it.

Then explore `dqlab_mysql > default > dqlab`: three tables, their columns and types. Click Run on the Metadata agent any time you want to re-ingest.

## 4. Run auto classification for sample data

Edit the AutoClassification agent that AutoPilot created (`⋮` > Edit). Turn on Store Sample Data, turn off Enable Auto Classification, and set the schedule to On Demand. Save, then click Run. If the agent isn't there yet, add one yourself on the Agents tab with the same settings, and delete AutoPilot's copy when it appears an hour later. Each table gets a Sample Data tab with 50 rows (the Row Limit dropdown above it is only a display limit). In OpenMetadata 2.x this is the only pipeline that stores table sample data.

Enable Auto Classification (PII tagging) stays off in this lab. It downloads a spaCy language model from GitHub the first time it runs, and networks that inspect TLS block that download. On an open network, you can turn it on to get suggested PII tags on columns such as `email` and `full_name`.

## 5. Enrich the catalog

Add descriptions to tables and columns, set an owner, apply a tag or two, and create a glossary term (for example "Order", linked to `orders`).

## 6. Run the profiler

Edit the Profiler agent that AutoPilot created (`⋮` > Edit) and make two changes:

- **Remove the classification filter.** AutoPilot's profiler only profiles tables tagged `Tier1` or `Tier2` (Filter Patterns > classification filter). None of the lab's tables are, so the run succeeds but profiles nothing ("Processed records: 0, Filtered: 3" in the logs). Delete both entries.
- Set the schedule to On Demand.

If the agent isn't there yet, add a Profiler agent yourself with those settings, and delete AutoPilot's copy when it appears an hour later. Save and click Run. On each table, Data Observability > Table Profile shows the row count, which matches the seeder's `total` column. Column Profile shows nulls, distinct values and min/max per column.

## 7. Create the tests and run them: everything green

Create the 13 tests in [the test table](reference.md#tests-and-the-defects-they-catch). For each one, open the table, go to Data Observability, add a test case, and give it exactly the name, column, type and parameters in the table. Turn on Compute Row Count for each.

Then go to Data Quality > Test Suites and create a Bundle Suite named `dqlab_mysql_suite`. A Bundle Suite is OpenMetadata's name for a logical test suite, and it can span tables. Add all 13 test cases, add a pipeline with an On Demand schedule, and run it. All 13 tests pass.

Shortcut: [run the three `dq_tests_*.yaml` files](reference.md#pipelines-from-yaml) to create the test cases (this needs the ingestion bot's token in `.env`), then build the Bundle Suite in the UI. The test names match, so nothing is duplicated.

## 8. Seed a bad batch and triage

```sh
python seed/seed.py --bad-rate 0.15
```

Re-run the Profiler agent (row counts grow) and the Bundle Suite pipeline. Tests go red, and each failed test opens an incident in the Incident Manager.

Compare every red test with the seeder's summary:
- A defect type with 0 rows leaves its test green. The products table only gets about 20 new rows per run, so it may not see every defect.
- Failed-row counts match the summary. The exception is uniqueness tests, which count both copies of each duplicate.

[Reading the results](reference.md#reading-the-results) explains the other quirks you may run into.

## 9. Investigate, fix and resolve

Red tests are the start of a process, not the end of one. This is the workflow a data team follows, and the order matters:

1. **Triage.** Open each failed test (Data Quality > Test Cases, or the Incident Manager). Read the failed-row count and look at the failed rows. Compare with the seeder's summary: the counts should match, except that uniqueness tests count both copies of a duplicate.
2. **Own the incident.** Acknowledge the incident, assign it to someone and set a severity. From now on there is a named owner and a record of what happened.
3. **Find the root cause.** Ask where the bad rows came from before touching them. In a real company the cause is usually an upstream application bug, a faulty load job or a schema change, and the table's owner and lineage tell you who to talk to. In this lab the cause is the seeder's bad batch.
4. **Fix at the source.** Correct the rows, or move them out, in the source database, and fix whatever produced them. Cleaning up the symptom only brings the same defects back on the next load. In the lab, the owners' fix is a script that removes every bad row the seeder can inject:

   ```sh
   python seed/fix_defects.py --dry-run   # count what would be fixed, change nothing
   python seed/fix_defects.py             # fix everything
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

## Troubleshooting

- **Auto classification fails with `CERTIFICATE_VERIFY_FAILED` for raw.githubusercontent.com**: this happens when Enable Auto Classification (PII tagging) is on. It downloads a spaCy language model (`en_core_web_md`) from GitHub the first time it runs, and networks that inspect TLS (corporate proxies) break that download. Turn it back off; sample data is still stored.
- **Profiler run succeeds but there are no profiles ("Processed records: 0, Filtered: 3")**: AutoPilot's Profiler agent has a classification filter limited to `Tier1`/`Tier2`, which none of the lab's tables match. Delete the filter entries, as described in item 6.
- **Lineage agent shows Failed**: expected. It needs query history (`mysql.general_log`), which the lab's user can't read. The lab doesn't use lineage, so delete the Lineage and Usage agents.
- **Two Profiler or two AutoClassification agents**: you added your own and AutoPilot added its copy an hour later. Keep one of each, configured as in items 4 and 6, and delete the other.
- **Can't connect to MySQL from the service wizard**: use `source-mysql:3306`, not `localhost`.
