# Reference

Lookup material for the lab: the tests and the defects they catch, the seeder, and the YAML pipelines. For the walkthrough, see the [learning path](learning-path.md).

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

`seed/seed.py` appends to the source database; it never truncates or updates. `seed/fix_defects.py` is its counterpart: it deletes the bad rows ([learning path, item 9](learning-path.md#9-investigate-fix-and-resolve)).

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

`fix_defects.py` takes one flag, `--dry-run`, which counts the bad rows and changes nothing.

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
