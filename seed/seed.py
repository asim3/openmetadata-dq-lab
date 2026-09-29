#!/usr/bin/env python3
"""Seed the lab's source databases with fake data, a share of it deliberately bad.

Run by hand from the repo root:

    python seed/seed.py --init --bad-rate 0 --days 7   # clean baseline
    python seed/seed.py --bad-rate 0.15                # "Monday's batch"

Append-only: every run inserts new rows and never updates or deletes old ones.
Credentials come from the environment or the repo's .env file.
"""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

try:
    import pymysql
    from faker import Faker
except ImportError as exc:
    sys.exit(f"seed.py: missing dependency '{exc.name}'. Run: pip install -r seed/requirements.txt")

import mysql_generators as gen
import mysql_schema as schema

REPO_ROOT = Path(__file__).resolve().parent.parent
MYSQL_HOST = "127.0.0.1"


class SeedError(Exception):
    """A problem the user can fix; reported without a traceback."""


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    if args.target != "mysql":
        print("seed.py: the Oracle target arrives in Phase 2; use --target mysql for now.", file=sys.stderr)
        return 2
    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    try:
        seed_mysql(args, seed)
    except SeedError as exc:
        print(f"seed.py: {exc}", file=sys.stderr)
        return 1
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Append fake data, a share of it deliberately bad, to the lab's source databases.",
    )
    parser.add_argument("--target", choices=("mysql", "oracle", "all"), default="mysql",
                        help="database(s) to seed (default: mysql)")
    parser.add_argument("--init", action="store_true",
                        help="create the tables first; safe to repeat")
    parser.add_argument("--customers", type=whole_number, default=500, metavar="N",
                        help="Phase 1 driver: new customers per run (default: 500)")
    parser.add_argument("--employees", type=whole_number, default=100, metavar="N",
                        help="Phase 2 driver: new employees per run (default: 100)")
    parser.add_argument("--bad-rate", type=fraction, default=0.10, metavar="R",
                        help="share of records that are bad, 0 to 1 (default: 0.10)")
    parser.add_argument("--days", type=positive_number, default=1, metavar="N",
                        help="spread the run across N back-dated days (default: 1)")
    parser.add_argument("--seed", type=int, metavar="N",
                        help="RNG seed; the same seed and starting data give the same batch")
    return parser.parse_args(argv)


def whole_number(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 or more")
    return value


def positive_number(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return value


def fraction(text: str) -> float:
    value = float(text)
    if not 0 <= value <= 1:
        raise argparse.ArgumentTypeError("must be between 0 and 1")
    return value


def load_dotenv(path: Path) -> None:
    """Read KEY=VALUE lines into os.environ; variables already set win."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def seed_mysql(args: argparse.Namespace, seed: int) -> None:
    rng = random.Random(seed)
    fake = Faker("en_US")
    fake.seed_instance(seed)
    port = int(os.environ.get("SOURCE_MYSQL_PORT", "3307"))

    conn = connect_mysql(port)
    try:
        with conn.cursor() as cur:
            created = schema.create_tables(cur) if args.init else []
            missing = [t for t in schema.TABLES if t not in schema.existing_tables(cur)]
            if missing:
                raise SeedError(f"table(s) {', '.join(missing)} not found in {schema.DATABASE}; run with --init first")
            existing = read_existing(cur)
            batch = gen.generate_batch(existing, args.customers, args.bad_rate, args.days, rng, fake)
            for table in schema.TABLES:
                columns = schema.COLUMNS[table]
                rows = [tuple(row[c] for c in columns) for row in batch.rows[table]]
                if rows:
                    cur.executemany(schema.insert_sql(table), rows)
        conn.commit()

        with conn.cursor() as cur:
            # OpenMetadata reads MySQL row counts from table statistics; refresh them.
            cur.execute(f"ANALYZE TABLE {', '.join(schema.TABLES)}")
            problems = [f"{t}: {msg}" for t, _op, kind, msg in cur.fetchall() if kind != "status" or msg != "OK"]
            totals = {}
            for table in schema.TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                totals[table] = cur.fetchone()[0]
    finally:
        conn.close()

    print_summary(port, existing.now, seed, args, created, batch, totals, problems)


def connect_mysql(port: int):
    user = require_env("SOURCE_MYSQL_USER")
    password = require_env("SOURCE_MYSQL_PASSWORD")
    try:
        return pymysql.connect(host=MYSQL_HOST, port=port, user=user, password=password,
                               database=schema.DATABASE, charset="utf8mb4", connect_timeout=10)
    except pymysql.err.OperationalError as exc:
        raise SeedError(
            f"cannot connect to source MySQL at {MYSQL_HOST}:{port} ({exc.args[-1]}). "
            "Is the stack up (docker compose up -d) and source-mysql healthy?"
        ) from exc


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SeedError(f"{name} is not set; copy .env.example to .env in the repo root")
    return value


def read_existing(cur) -> gen.ExistingData:
    # Timestamps are anchored to the server clock: the host's may be in another time zone.
    cur.execute("SELECT NOW()")
    (now,) = cur.fetchone()

    rows = {}
    for table in ("products", "customers"):
        columns = schema.COLUMNS[table]
        cur.execute(f"SELECT {', '.join(columns)} FROM {table} ORDER BY {columns[0]}")
        rows[table] = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.execute("SELECT COALESCE(MAX(order_id), 0) + 1 FROM orders")
    (next_order_id,) = cur.fetchone()

    return gen.ExistingData(
        now=now,
        products=rows["products"],
        customers=rows["customers"],
        next_order_id=int(next_order_id),
    )


def print_summary(port, now, seed, args, created, batch, totals, problems) -> None:
    print(f"Seeded MySQL {schema.DATABASE} at {MYSQL_HOST}:{port} (server time {now:%Y-%m-%d %H:%M:%S})")
    print(f"seed {seed}, bad-rate {args.bad_rate:g}, spread over {args.days} day(s)")
    if created:
        print(f"created tables: {', '.join(created)}")
    print()

    print(f"{'table':<11}{'inserted':>9}{'bad':>7}{'total':>9}")
    for table in schema.TABLES:
        bad = sum(n for (t, _defect), n in batch.defects.items() if t == table)
        print(f"{table:<11}{len(batch.rows[table]):>9}{bad:>7}{totals[table]:>9}")
    print()

    if not batch.defects:
        print("No bad rows in this run.")
    else:
        print(f"{'bad rows by defect':<42}{'rows':>5}   caught by test")
        for table, defects in gen.DEFECTS.items():
            for defect, test in defects.items():
                count = batch.defects[table, defect]
                split = sorted((c, n) for (t, d, c), n in batch.variants.items() if (t, d) == (table, defect))
                detail = f"  ({', '.join(f'{c} {n}' for c, n in split)})" if split else ""
                print(f"  {table:<10}{defect:<30}{count:>5}   {test}{detail}")
        if any(defect.startswith("duplicate") for _t, defect in batch.defects):
            print("  Uniqueness tests flag both copies: expect 2 failed rows per duplicate.")
    print()

    if problems:
        print("warning: ANALYZE TABLE reported: " + "; ".join(problems))
    else:
        print("Table statistics refreshed (ANALYZE TABLE), so OpenMetadata's row counts are current.")
    print(f"Reproduce this batch from the same starting data with --seed {seed}.")


if __name__ == "__main__":
    sys.exit(main())
