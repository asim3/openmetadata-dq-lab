#!/usr/bin/env python3
"""Fix the source data: remove every bad row the seeder can inject.

Run by hand from the repo root, after the owners have been "ticketed":

    python seed/fix_defects.py             # fix everything
    python seed/fix_defects.py --dry-run   # only count what would be fixed

The fix is a delete, the simplest repair for a lab: a bad row is removed, and for
a duplicate the row with the higher id goes. Safe to repeat: with nothing left to
fix it changes nothing. Credentials come from the environment or the repo's .env.
"""

from __future__ import annotations

import argparse
import os
import sys

import mysql_generators as gen
import mysql_schema as schema
import seed

# (table, primary key, defect, "JOIN ... WHERE ..." on the table aliased as t)
# Order matters: customers and products go first, so orders that pointed at a
# deleted row are caught by the orphan rule at the end.
_COUNTRIES = ", ".join(f"'{c}'" for c in gen.COUNTRIES)
_STATUSES = ", ".join(f"'{s}'" for s in gen.ORDER_STATUSES)
FIXES = [
    ("customers", "customer_id", "null full_name", "WHERE t.full_name IS NULL"),
    ("customers", "customer_id", "duplicate email",
     "JOIN customers k ON k.email = t.email AND k.customer_id < t.customer_id"),
    ("customers", "customer_id", "malformed email", "WHERE t.email NOT REGEXP %(email_regex)s"),
    ("customers", "customer_id", "age outside 18-90",
     f"WHERE t.age < {gen.MIN_AGE} OR t.age > {gen.MAX_AGE}"),
    ("customers", "customer_id", "country not allowed", f"WHERE t.country NOT IN ({_COUNTRIES})"),
    ("products", "product_id", "duplicate sku",
     "JOIN products k ON k.sku = t.sku AND k.product_id < t.product_id"),
    ("products", "product_id", "unit_price <= 0", "WHERE t.unit_price <= 0"),
    ("products", "product_id", "null category", "WHERE t.category IS NULL"),
    ("orders", "order_id", "amount/quantity <= 0", "WHERE t.amount <= 0 OR t.quantity <= 0"),
    ("orders", "order_id", "status not allowed", f"WHERE t.status NOT IN ({_STATUSES})"),
    ("orders", "order_id", "future order_date", "WHERE t.order_date > NOW()"),
    ("orders", "order_id", "orphan customer_id/product_id",
     "WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.customer_id = t.customer_id)"
     " OR NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = t.product_id)"),
]
PARAMS = {"email_regex": gen.EMAIL_REGEX}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove the bad rows the seeder injects from the lab's MySQL source.")
    parser.add_argument("--dry-run", action="store_true", help="count the bad rows without deleting anything")
    args = parser.parse_args(argv)

    seed.load_dotenv(seed.REPO_ROOT / ".env")
    try:
        fix_mysql(args.dry_run)
    except seed.SeedError as exc:
        print(f"fix_defects.py: {exc}", file=sys.stderr)
        return 1
    return 0


def fix_mysql(dry_run: bool) -> None:
    port = int(os.environ.get("SOURCE_MYSQL_PORT", "3307"))
    conn = seed.connect_mysql(port)
    try:
        with conn.cursor() as cur:
            missing = [t for t in schema.TABLES if t not in schema.existing_tables(cur)]
            if missing:
                raise seed.SeedError(f"table(s) {', '.join(missing)} not found in {schema.DATABASE}")
            before = row_counts(cur)

            print(f"{'table':<11}{'defect':<32}{'rows':>6}")
            fixed = {t: 0 for t in schema.TABLES}
            for table, pk, defect, clause in FIXES:
                cur.execute(f"SELECT COUNT(DISTINCT t.{pk}) FROM {table} t {clause}", PARAMS)
                (count,) = cur.fetchone()
                if count and not dry_run:
                    cur.execute(f"DELETE t FROM {table} t {clause}", PARAMS)
                    count = cur.rowcount
                    fixed[table] += count
                print(f"{table:<11}{defect:<32}{count:>6}")
            if dry_run:
                conn.rollback()
            else:
                conn.commit()
                # OpenMetadata reads MySQL row counts from table statistics; refresh them.
                cur.execute(f"ANALYZE TABLE {', '.join(schema.TABLES)}")
                cur.fetchall()
            after = row_counts(cur)
    finally:
        conn.close()

    print()
    print(f"{'table':<11}{'before':>8}{'after':>8}")
    for table in schema.TABLES:
        print(f"{table:<11}{before[table]:>8}{after[table]:>8}")
    print()
    if dry_run:
        print("Dry run: nothing was changed.")
    else:
        print("Fixed. Re-run the Profiler agent and the Bundle Suite pipeline: every test should be green.")


def row_counts(cur) -> dict[str, int]:
    counts = {}
    for table in schema.TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cur.fetchone()[0]
    return counts


if __name__ == "__main__":
    sys.exit(main())
