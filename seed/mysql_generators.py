"""Clean and bad records for the Phase 1 MySQL e-commerce source.

Every bad record gets exactly one defect, picked at random from its table's
list, and each defect maps to the OpenMetadata test that should catch it.

What keeps clean data clean, so a --bad-rate 0 run passes every test:
- email and sku embed the row id, so they stay unique across runs, even when
  the same --seed is reused;
- timestamps come from the MySQL server clock, never the host's;
- clean orders only reference products with a valid price;
- bad values differ from allowed ones by more than letter case or accents,
  because MySQL's default collation compares 'PENDING' equal to 'pending'.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

# Rules the OpenMetadata tests check; pipelines/mysql/dq_tests_*.yaml use the
# same values.
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}$"
COUNTRIES = {"SA": 40, "AE": 15, "KW": 8, "EG": 8, "QA": 6, "BH": 5, "OM": 5, "JO": 5, "GB": 4, "US": 4}
ORDER_STATUSES = {"delivered": 55, "shipped": 20, "pending": 15, "cancelled": 10}
MIN_AGE, MAX_AGE = 18, 90
MIN_PRICE = Decimal("1.00")  # the tests use minValue 1: the UI takes whole numbers

# defect -> the OpenMetadata test that catches it
DEFECTS = {
    "products": {
        "duplicate sku": "products_sku_unique",
        "unit_price <= 0": "products_unit_price_min_1",
        "null category": "products_category_not_null",
    },
    "customers": {
        "null full_name": "customers_full_name_not_null",
        "duplicate email": "customers_email_unique",
        "malformed email": "customers_email_format",
        "age outside 18-90": "customers_age_between_18_and_90",
        "country not allowed": "customers_country_allowed",
    },
    "orders": {
        "orphan customer_id/product_id": "orders_no_orphans",
        "amount/quantity <= 0": "orders_amount_min_1 / orders_quantity_min_1",
        "status not allowed": "orders_status_allowed",
        "future order_date": "orders_no_future_dates",
    },
}

BAD_COUNTRIES = ("KSA", "UAE", "UK", "USA", "Saudi Arabia", "United Kingdom", "N/A", "XX", "")
BAD_STATUSES = ("canceled", "returned", "refunded", "shipping", "complete", "on hold", "unknown", "")
# Ids no real row will reach: the lab would need 90 million customers first.
ORPHAN_ID_BASE = 90_000_000

CATEGORIES = {
    # category: (sku prefix, min price, max price, product nouns)
    "Electronics": ("ELE", 15, 1500, ("Wireless Earbuds", "Bluetooth Speaker", "USB-C Charger", "Smart Watch", "Power Bank", "Laptop Stand", "Webcam")),
    "Books": ("BOO", 5, 80, ("Cookbook", "Travel Guide", "Mystery Novel", "Coding Handbook", "Children's Atlas", "Poetry Collection")),
    "Home & Kitchen": ("HOM", 5, 400, ("Chef's Knife", "Coffee Grinder", "Cast Iron Pan", "Table Lamp", "Storage Box", "Kettle")),
    "Toys": ("TOY", 3, 150, ("Puzzle", "Building Blocks", "Plush Bear", "Kite", "Board Game", "Toy Car")),
    "Sports": ("SPO", 5, 600, ("Yoga Mat", "Running Shoes", "Dumbbell Set", "Water Bottle", "Tennis Racket", "Cycling Helmet")),
    "Beauty": ("BEA", 3, 200, ("Face Serum", "Hair Dryer", "Lip Balm", "Perfume", "Sunscreen", "Beard Oil")),
    "Grocery": ("GRO", 1, 60, ("Arabic Coffee", "Dates Box", "Olive Oil", "Green Tea", "Honey Jar", "Basmati Rice")),
}
PRODUCT_ADJECTIVES = ("Classic", "Pro", "Mini", "Ultra", "Eco", "Deluxe", "Essential", "Premium", "Compact", "Everyday")
EMAIL_DOMAINS = ("example.com", "example.net", "example.org", "mail.example.com")

FIRST_RUN_PRODUCTS = 200
PRODUCTS_PER_RUN = (15, 25)
ORDERS_PER_CUSTOMER = (2.7, 3.3)
QUANTITY_WEIGHTS = {1: 50, 2: 25, 3: 12, 4: 8, 5: 5}

_EMAIL_PATTERN = re.compile(EMAIL_REGEX)
_CENT = Decimal("0.01")


@dataclass
class ExistingData:
    """Rows already in the database that a new batch builds on."""

    now: datetime  # MySQL server clock
    products: list[dict]  # every row, ordered by product_id
    customers: list[dict]  # every row, ordered by customer_id
    next_order_id: int


@dataclass
class Batch:
    rows: dict[str, list[dict]] = field(default_factory=dict)
    defects: Counter = field(default_factory=Counter)  # (table, defect) -> rows
    variants: Counter = field(default_factory=Counter)  # (table, defect, column) -> rows

    def record(self, table: str, defect: str, column: str | None = None) -> None:
        self.defects[table, defect] += 1
        if column:
            self.variants[table, defect, column] += 1


class Clock:
    """Timestamps spread over the last `days` days, never after the server's `now`."""

    def __init__(self, now: datetime, days: int, rng: Random):
        self.now, self.days, self.rng = now, days, rng

    def timestamp(self, not_before: datetime | None = None) -> datetime:
        day = datetime.combine(self.now.date() - timedelta(days=self.rng.randrange(self.days)), time.min)
        end = min(day + timedelta(days=1, seconds=-1), self.now)
        ts = day + timedelta(seconds=self.rng.randint(0, int((end - day).total_seconds())))
        if not_before is not None and ts < not_before <= self.now:
            ts = not_before + timedelta(seconds=self.rng.randint(0, int((self.now - not_before).total_seconds())))
        return ts

    def future(self) -> datetime:
        return self.now + timedelta(days=self.rng.randint(60, 730), seconds=self.rng.randint(0, 86_399))


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_PATTERN.fullmatch(email))


def generate_batch(data: ExistingData, customers: int, bad_rate: float, days: int, rng: Random, fake: Faker) -> Batch:
    clock = Clock(data.now, days, rng)
    batch = Batch()
    _products(data, batch, bad_rate, clock, rng)
    _customers(data, batch, customers, bad_rate, clock, rng, fake)
    _orders(data, batch, round(customers * rng.uniform(*ORDERS_PER_CUSTOMER)), bad_rate, clock, rng)
    return batch


def _products(data: ExistingData, batch: Batch, bad_rate: float, clock: Clock, rng: Random) -> None:
    count = rng.randint(*PRODUCTS_PER_RUN) if data.products else FIRST_RUN_PRODUCTS
    first_id = _next_id(data.products, "product_id")
    rows = []
    for i in range(count):
        product_id = first_id + i
        category = rng.choice(list(CATEGORIES))
        prefix, low, high, nouns = CATEGORIES[category]
        rows.append({
            "product_id": product_id,
            "sku": f"{prefix}-{product_id:06d}",
            "name": f"{rng.choice(PRODUCT_ADJECTIVES)} {rng.choice(nouns)}",
            "category": category,
            "unit_price": _price(rng, low, high),
            "created_at": clock.timestamp(),
        })

    bad = _pick_bad(len(rows), bad_rate, rng)
    duplicate_sources = _duplicate_sources("sku", data.products, _clean_product, rows, bad)
    for i in bad:
        row = rows[i]
        defect = _pick_defect("products", rng, can_duplicate=bool(duplicate_sources))
        if defect == "duplicate sku":
            row["sku"] = _pop(duplicate_sources, rng)
        elif defect == "unit_price <= 0":
            row["unit_price"] = rng.choice((Decimal("0.00"), -row["unit_price"]))
        else:
            row["category"] = None
        batch.record("products", defect)
    batch.rows["products"] = rows


def _customers(data: ExistingData, batch: Batch, count: int, bad_rate: float, clock: Clock, rng: Random, fake: Faker) -> None:
    first_id = _next_id(data.customers, "customer_id")
    rows = []
    for i in range(count):
        customer_id = first_id + i
        first, last = fake.first_name(), fake.last_name()
        rows.append({
            "customer_id": customer_id,
            "full_name": f"{first} {last}",
            "email": f"{_slug(first)}.{_slug(last)}.{customer_id}@{rng.choice(EMAIL_DOMAINS)}",
            "age": int(rng.triangular(MIN_AGE, MAX_AGE, 34)),
            "country": _weighted(COUNTRIES, rng),
            "created_at": clock.timestamp(),
        })

    bad = _pick_bad(len(rows), bad_rate, rng)
    duplicate_sources = _duplicate_sources("email", data.customers, _clean_customer, rows, bad)
    for i in bad:
        row = rows[i]
        defect = _pick_defect("customers", rng, can_duplicate=bool(duplicate_sources))
        if defect == "null full_name":
            row["full_name"] = None
        elif defect == "duplicate email":
            row["email"] = _pop(duplicate_sources, rng)
        elif defect == "malformed email":
            row["email"] = _malformed_email(row["email"], rng)
        elif defect == "age outside 18-90":
            row["age"] = rng.randint(-5, MIN_AGE - 1) if rng.random() < 0.5 else rng.randint(MAX_AGE + 1, 150)
        else:
            row["country"] = rng.choice(BAD_COUNTRIES)
        batch.record("customers", defect)
    batch.rows["customers"] = rows


def _orders(data: ExistingData, batch: Batch, count: int, bad_rate: float, clock: Clock, rng: Random) -> None:
    customers = data.customers + batch.rows["customers"]
    # Only products with a valid price, so a bad product never makes a clean order fail.
    products = [row for row in data.products + batch.rows["products"] if _valid_price(row)]
    rows = []
    for i in range(count if customers and products else 0):
        customer = rng.choice(customers)
        product = rng.choice(products)
        quantity = _weighted(QUANTITY_WEIGHTS, rng)
        since = [t for t in (customer["created_at"], product["created_at"]) if t is not None]
        rows.append({
            "order_id": data.next_order_id + i,
            "customer_id": customer["customer_id"],
            "product_id": product["product_id"],
            "quantity": quantity,
            "amount": (product["unit_price"] * quantity).quantize(_CENT),
            "status": _weighted(ORDER_STATUSES, rng),
            "order_date": clock.timestamp(not_before=max(since, default=None)),
        })

    for i in _pick_bad(len(rows), bad_rate, rng):
        row = rows[i]
        defect = _pick_defect("orders", rng)
        column = None
        if defect == "orphan customer_id/product_id":
            column = rng.choice(("customer_id", "product_id"))
            row[column] = ORPHAN_ID_BASE + rng.randrange(10_000_000)
        elif defect == "amount/quantity <= 0":
            column = rng.choice(("amount", "quantity"))
            row[column] = rng.choice((0 * row[column], -row[column]))
        elif defect == "status not allowed":
            row["status"] = rng.choice(BAD_STATUSES)
        else:
            row["order_date"] = clock.future()
        batch.record("orders", defect, column)
    batch.rows["orders"] = rows


def _pick_bad(count: int, bad_rate: float, rng: Random) -> list[int]:
    return sorted(rng.sample(range(count), round(count * bad_rate)))


def _next_id(rows: list[dict], key: str) -> int:
    return max((row[key] for row in rows), default=0) + 1


def _valid_price(product: dict) -> bool:
    return product["unit_price"] is not None and product["unit_price"] >= MIN_PRICE


def _clean_product(product: dict) -> bool:
    return _valid_price(product) and product["category"] is not None


def _clean_customer(customer: dict) -> bool:
    return (
        customer["full_name"] is not None
        and customer["email"] is not None
        and is_valid_email(customer["email"])
        and customer["age"] is not None
        and MIN_AGE <= customer["age"] <= MAX_AGE
        and customer["country"] in COUNTRIES
    )


def _duplicate_sources(column: str, existing: list[dict], is_clean, new_rows: list[dict], bad: list[int]) -> list[str]:
    """Values a duplicate may copy: still unique, on a row with no other defect.

    That way every duplicate adds exactly one clashing pair, and no row ends up
    failing two tests. MySQL compares case-insensitively, hence casefold().
    """
    counts = Counter(row[column].casefold() for row in existing if row[column] is not None)
    sources = [
        row[column]
        for row in existing
        if row[column] is not None and counts[row[column].casefold()] == 1 and is_clean(row)
    ]
    bad_rows = set(bad)
    return sources + [row[column] for i, row in enumerate(new_rows) if i not in bad_rows]


def _pick_defect(table: str, rng: Random, can_duplicate: bool = True) -> str:
    # A duplicate needs a clean, still-unique value to copy; without one, pick another defect.
    options = [d for d in DEFECTS[table] if can_duplicate or not d.startswith("duplicate")]
    return rng.choice(options)


def _pop(values: list[str], rng: Random) -> str:
    # Each source is copied once, so every duplicate adds exactly one clashing pair.
    return values.pop(rng.randrange(len(values)))


def _weighted(weights: dict, rng: Random):
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def _price(rng: Random, low: float, high: float) -> Decimal:
    # Log-uniform: many cheap items, a few expensive ones.
    return Decimal(f"{low * (high / low) ** rng.random():.2f}")


def _slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower()) or "user"


def _malformed_email(email: str, rng: Random) -> str:
    # Built from the row's own clean email, so it keeps the row id and stays unique.
    local, domain = email.split("@", 1)
    return rng.choice((
        f"{local}{domain}",  # missing @
        f"{local}@@{domain}",  # double @
        f"{local}@{domain.split('.', 1)[0]}",  # no top-level domain
        f"{local}@{domain.replace('.', ',')}",  # comma for a dot
        f"{local.replace('.', ' ', 1)}@{domain}",  # space in the name
    ))
