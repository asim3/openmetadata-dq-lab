"""E-commerce schema for the Phase 1 MySQL source (database `dqlab`).

The tables are deliberately loose: primary keys only, no FOREIGN KEY, UNIQUE or
NOT NULL constraints, so bad rows land in the database and it's OpenMetadata's
quality tests that catch them.
"""

from __future__ import annotations

DATABASE = "dqlab"

# Insert order; orders reference the other two (by convention only).
TABLES = ("products", "customers", "orders")

COLUMNS = {
    "products": ("product_id", "sku", "name", "category", "unit_price", "created_at"),
    "customers": ("customer_id", "full_name", "email", "age", "country", "created_at"),
    "orders": ("order_id", "customer_id", "product_id", "quantity", "amount", "status", "order_date"),
}

DDL = {
    "products": """
        CREATE TABLE IF NOT EXISTS products (
            product_id  INT AUTO_INCREMENT PRIMARY KEY,
            sku         VARCHAR(32),
            name        VARCHAR(255),
            category    VARCHAR(64),
            unit_price  DECIMAL(10, 2),
            created_at  DATETIME
        )
    """,
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name   VARCHAR(255),
            email       VARCHAR(255),
            age         INT,
            country     VARCHAR(64),
            created_at  DATETIME
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            order_id    INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT,
            product_id  INT,
            quantity    INT,
            amount      DECIMAL(12, 2),
            status      VARCHAR(32),
            order_date  DATETIME
        )
    """,
}


def existing_tables(cursor) -> set[str]:
    cursor.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
        (DATABASE,),
    )
    return {name.lower() for (name,) in cursor.fetchall()}


def create_tables(cursor) -> list[str]:
    """Create any missing tables; return the names of the ones created."""
    before = existing_tables(cursor)
    for table in TABLES:
        cursor.execute(DDL[table])
    return [table for table in TABLES if table not in before]


def insert_sql(table: str) -> str:
    columns = COLUMNS[table]
    placeholders = ", ".join(["%s"] * len(columns))
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
