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
import oracle_generators as ogen
import oracle_schema as oschema
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

# Oracle: (table, primary key, defect, "WHERE ..." on the table aliased as t).
# Employees go first; child rows left without an employee are removed last.
_STATUS_CODES = ", ".join(f"'{s}'" for s in ogen.STATUSES)
_ALLOWANCE_TYPES = ", ".join(f"'{t}'" for t in ogen.ALLOWANCE_TYPES)
_NO_EMPLOYEE = "WHERE NOT EXISTS (SELECT 1 FROM EMPLOYEES e WHERE e.EMP_ID = t.EMP_ID)"
ORACLE_FIXES = [
    ("EMPLOYEES", "EMP_ID", "null FULL_NAME", "WHERE t.FULL_NAME IS NULL"),
    ("EMPLOYEES", "EMP_ID", "duplicate STAFF_NO",
     "WHERE EXISTS (SELECT 1 FROM EMPLOYEES k WHERE k.STAFF_NO = t.STAFF_NO AND k.EMP_ID < t.EMP_ID)"),
    ("EMPLOYEES", "EMP_ID", "HIRE_DATE not YYYY-MM-DD", "WHERE NOT REGEXP_LIKE(t.HIRE_DATE, :hire_date_regex)"),
    ("EMPLOYEES", "EMP_ID", "STATUS not A/T", f"WHERE t.STATUS NOT IN ({_STATUS_CODES})"),
    ("EMPLOYEES", "EMP_ID", "orphan DEPT_ID",
     "WHERE NOT EXISTS (SELECT 1 FROM DEPARTMENTS d WHERE d.DEPT_ID = t.DEPT_ID)"),
    ("EMPLOYEES", "EMP_ID", "DEPT_NAME differs from master",
     "WHERE EXISTS (SELECT 1 FROM DEPARTMENTS d WHERE d.DEPT_ID = t.DEPT_ID AND d.DEPT_NAME <> t.DEPT_NAME)"),
    ("JOB_HISTORY", "JH_ID", "END_DATE before START_DATE", "WHERE t.END_DATE < t.START_DATE"),
    ("SALARIES", "SAL_ID", "BASE_AMOUNT <= 0 or absurdly high",
     f"WHERE t.BASE_AMOUNT < {ogen.MIN_BASE} OR t.BASE_AMOUNT > {ogen.MAX_BASE}"),
    ("SALARIES", "SAL_ID", "CURRENCY not SAR", f"WHERE t.CURRENCY <> '{ogen.CURRENCY}'"),
    ("ALLOWANCES", "ALW_ID", "invalid ALW_TYPE", f"WHERE t.ALW_TYPE NOT IN ({_ALLOWANCE_TYPES})"),
    ("ALLOWANCES", "ALW_ID", "negative AMOUNT", "WHERE t.AMOUNT < 0"),
    ("SALARIES", "SAL_ID", "orphan EMP_ID", _NO_EMPLOYEE),
    ("JOB_HISTORY", "JH_ID", "orphan EMP_ID (employee deleted)", _NO_EMPLOYEE),
    ("ALLOWANCES", "ALW_ID", "orphan EMP_ID (employee deleted)", _NO_EMPLOYEE),
]
ORACLE_PARAMS = {"hire_date_regex": ogen.HIRE_DATE_REGEX}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Remove the bad rows the seeder injects from the lab's source databases.")
    parser.add_argument("--target", choices=("mysql", "oracle", "all"), default="mysql",
                        help="database(s) to fix (default: mysql)")
    parser.add_argument("--dry-run", action="store_true", help="count the bad rows without deleting anything")
    args = parser.parse_args(argv)

    seed.load_dotenv(seed.REPO_ROOT / ".env")
    try:
        if args.target in ("mysql", "all"):
            fix_mysql(args.dry_run)
        if args.target in ("oracle", "all"):
            if args.target == "all":
                print()
            fix_oracle(args.dry_run)
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


def fix_oracle(dry_run: bool) -> None:
    port = int(os.environ.get("SOURCE_ORACLE_PORT", "1521"))
    conn = seed.connect_oracle(port)
    try:
        with conn.cursor() as cur:
            missing = [t for t in oschema.TABLES if t not in oschema.existing_objects(cur, "TABLE")]
            if missing:
                raise seed.SeedError(f"table(s) {', '.join(missing)} not found in schema {conn.username.upper()}")
            before = oracle_row_counts(cur)

            print(f"{'table':<13}{'defect':<36}{'rows':>6}")
            for table, pk, defect, clause in ORACLE_FIXES:
                params = {k: v for k, v in ORACLE_PARAMS.items() if f":{k}" in clause}
                ids = f"SELECT DISTINCT t.{pk} FROM {table} t {clause}"
                cur.execute(f"SELECT COUNT(*) FROM ({ids})", params)
                (count,) = cur.fetchone()
                if count and not dry_run:
                    cur.execute(f"DELETE FROM {table} WHERE {pk} IN ({ids})", params)
                    count = cur.rowcount
                print(f"{table:<13}{defect:<36}{count:>6}")
            if dry_run:
                conn.rollback()
            else:
                conn.commit()
                cur.execute("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS(USER); END;")
            after = oracle_row_counts(cur)
    finally:
        conn.close()

    print()
    print(f"{'table':<13}{'before':>8}{'after':>8}")
    for table in oschema.TABLES:
        print(f"{table:<13}{before[table]:>8}{after[table]:>8}")
    print()
    if dry_run:
        print("Dry run: nothing was changed.")
    else:
        print("Fixed. Re-run the Profiler agent and the Oracle Bundle Suite pipeline: every test should be green.")


def oracle_row_counts(cur) -> dict[str, int]:
    counts = {}
    for table in oschema.TABLES:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cur.fetchone()[0]
    return counts


if __name__ == "__main__":
    sys.exit(main())
