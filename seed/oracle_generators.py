"""Clean and bad records for the Phase 2 Oracle legacy HR source.

Every bad record gets exactly one defect, picked at random from its table's
list, and each defect maps to the OpenMetadata test that should catch it.

What keeps clean data clean, so a --bad-rate 0 run passes every test:
- STAFF_NO embeds the employee id, so it stays unique across runs;
- dates come from the Oracle server clock, never the host's;
- a clean EMPLOYEES.DEPT_NAME is copied from DEPARTMENTS at insert time;
- Oracle compares strings case-sensitively and stores '' as NULL, so a "blank"
  status is a single space, and a lowercase 'a' really is a different value.

Legacy quirks (exactly three), each with a defect that breaks it:
1. EMPLOYEES.HIRE_DATE is VARCHAR2, mostly YYYY-MM-DD;
2. EMPLOYEES.STATUS is CHAR(1): A active, T terminated;
3. EMPLOYEES.DEPT_NAME is a copy of DEPARTMENTS.DEPT_NAME.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from random import Random

from faker import Faker

from mysql_generators import Batch

# Rules the OpenMetadata tests check; the test tables in docs/reference.md use the
# same values.
HIRE_DATE_REGEX = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
STATUSES = {"A": 90, "T": 10}
CURRENCY = "SAR"
ALLOWANCE_TYPES = ("HOUSING", "TRANSPORT", "OTHER")
MIN_BASE, MAX_BASE = 1, 100_000  # the tests use whole numbers: the UI takes no decimals

# defect -> the OpenMetadata test that catches it
DEFECTS = {
    "EMPLOYEES": {
        "null FULL_NAME": "employees_full_name_not_null",
        "duplicate STAFF_NO": "employees_staff_no_unique",
        "HIRE_DATE not YYYY-MM-DD": "employees_hire_date_format",
        "STATUS not A/T": "employees_status_allowed",
        "orphan DEPT_ID": "employees_no_orphan_dept",
        "DEPT_NAME differs from master": "employees_dept_name_matches_master",
    },
    "JOB_HISTORY": {
        "END_DATE before START_DATE": "job_history_end_after_start",
    },
    "SALARIES": {
        "BASE_AMOUNT <= 0 or absurdly high": "salaries_base_amount_between_1_and_100000",
        "CURRENCY not SAR": "salaries_currency_sar",
        "orphan EMP_ID": "salaries_no_orphan_emp",
    },
    "ALLOWANCES": {
        "invalid ALW_TYPE": "allowances_type_allowed",
        "negative AMOUNT": "allowances_amount_min_0",
    },
}

DEPARTMENTS = (
    # name, job titles
    ("Human Resources", ("HR Officer", "HR Manager", "Recruiter")),
    ("Finance", ("Accountant", "Senior Accountant", "Finance Manager")),
    ("Information Technology", ("Developer", "Systems Administrator", "IT Manager")),
    ("Operations", ("Operations Officer", "Shift Supervisor", "Operations Manager")),
    ("Sales", ("Sales Representative", "Account Manager", "Sales Director")),
    ("Marketing", ("Marketing Specialist", "Brand Manager", "Content Writer")),
    ("Procurement", ("Buyer", "Procurement Officer", "Category Manager")),
    ("Legal", ("Legal Counsel", "Paralegal", "Compliance Officer")),
    ("Customer Support", ("Support Agent", "Team Lead", "Support Manager")),
    ("Logistics", ("Dispatcher", "Warehouse Clerk", "Logistics Manager")),
    ("Maintenance", ("Technician", "Electrician", "Maintenance Supervisor")),
    ("Administration", ("Administrative Assistant", "Office Manager", "Receptionist")),
)

# pay grade: (min base, max base)
PAY_GRADES = {"G1": (3000, 5000), "G2": (5000, 8000), "G3": (8000, 12000),
              "G4": (12000, 18000), "G5": (18000, 28000), "G6": (28000, 45000)}
ALLOWANCE_RANGES = {"HOUSING": (1500, 6000), "TRANSPORT": (300, 1200), "OTHER": (100, 800)}

BAD_STATUSES = ("a", "t", " ", "X", "1", "?")
BAD_CURRENCIES = ("USD", "EUR", "AED", "sar", "SR", "XXX")
BAD_ALLOWANCE_TYPES = ("Housing", "MEAL", "BONUS", "TRANSPORTATION", "N/A", "??")
# Ids no real row will reach: the lab would need 90 million employees first, and
# DEPT_ID is NUMBER(6), so a department id has less room.
ORPHAN_ID_BASE = 90_000_000
ORPHAN_DEPT_BASE = 900_000

_HIRE_DATE_PATTERN = re.compile(HIRE_DATE_REGEX)
_CENT = Decimal("0.01")


@dataclass
class ExistingData:
    """Rows already in the database that a new batch builds on."""

    now: datetime  # Oracle server clock
    departments: list[dict]  # every row, ordered by DEPT_ID
    employees: list[dict]  # every row, ordered by EMP_ID
    next_ids: dict[str, int]  # table -> next primary key


def generate_batch(data: ExistingData, employees: int, bad_rate: float, days: int, rng: Random, fake: Faker) -> Batch:
    batch = Batch()
    today = data.now.date()
    departments = _departments(data, batch)
    master = {d["DEPT_ID"]: d for d in departments}
    titles = {name: jobs for name, jobs in DEPARTMENTS}

    emp_rows, jh_rows, sal_rows, alw_rows = [], [], [], []
    ids = dict(data.next_ids)
    for i in range(employees):
        emp_id = ids["EMPLOYEES"] + i
        dept = rng.choice(departments)
        job_title = rng.choice(titles[dept["DEPT_NAME"]])
        hire = today - timedelta(days=rng.randint(365, 365 * 12))
        emp_rows.append({
            "EMP_ID": emp_id,
            "STAFF_NO": f"E{emp_id:06d}",
            "FULL_NAME": f"{fake.first_name()} {fake.last_name()}",
            "DEPT_ID": dept["DEPT_ID"],
            "DEPT_NAME": dept["DEPT_NAME"],
            "HIRE_DATE": hire.isoformat(),
            "JOB_TITLE": job_title,
            "STATUS": _weighted(STATUSES, rng),
        })
        batch_day = today - timedelta(days=rng.randrange(days))
        _history(emp_id, hire, today, dept, job_title, departments, titles, ids, jh_rows, rng)
        _salaries(emp_id, hire, batch_day, ids, sal_rows, rng)
        _allowances(emp_id, batch_day, ids, alw_rows, rng)

    _employee_defects(data, batch, emp_rows, master, bad_rate, rng)
    _job_history_defects(batch, jh_rows, bad_rate, rng)
    _salary_defects(batch, sal_rows, bad_rate, rng)
    _allowance_defects(batch, alw_rows, bad_rate, rng)
    batch.rows.update({"EMPLOYEES": emp_rows, "JOB_HISTORY": jh_rows, "SALARIES": sal_rows, "ALLOWANCES": alw_rows})
    return batch


def _departments(data: ExistingData, batch: Batch) -> list[dict]:
    """DEPARTMENTS is seeded once; later runs reuse the rows."""
    if data.departments:
        batch.rows["DEPARTMENTS"] = []
        return data.departments
    rows = [
        {"DEPT_ID": 10 * (i + 1), "DEPT_NAME": name, "COST_CENTER": f"CC{1000 + 10 * (i + 1)}"}
        for i, (name, _titles) in enumerate(DEPARTMENTS)
    ]
    batch.rows["DEPARTMENTS"] = rows
    return rows


def _history(emp_id, hire, today, dept, job_title, departments, titles, ids, rows, rng) -> None:
    """1-3 jobs in a chain from the hire date; the last has no END_DATE and matches EMPLOYEES."""
    count = rng.randint(1, 3)
    span = (today - hire).days
    starts = [hire] + [hire + timedelta(days=d) for d in sorted(rng.sample(range(30, span - 30), count - 1))]
    for n, start in enumerate(starts):
        last = n == count - 1
        if last:
            job_dept, title = dept, job_title
        else:
            job_dept = rng.choice(departments)
            title = rng.choice(titles[job_dept["DEPT_NAME"]])
        rows.append({
            "JH_ID": ids["JOB_HISTORY"] + len(rows),
            "EMP_ID": emp_id,
            "DEPT_ID": job_dept["DEPT_ID"],
            "JOB_TITLE": title,
            "START_DATE": start,
            "END_DATE": None if last else starts[n + 1] - timedelta(days=1),
        })


def _salaries(emp_id, hire, batch_day, ids, rows, rng) -> None:
    grade = rng.choice(list(PAY_GRADES))
    base = Decimal(rng.randint(*PAY_GRADES[grade]))
    entries = [(base, hire)]
    if rng.random() < 0.5:  # a raise, effective on this batch's day
        entries = [(base, hire), ((base * Decimal("1.08")).quantize(_CENT), batch_day)]
    for amount, effective in entries:
        rows.append({
            "SAL_ID": ids["SALARIES"] + len(rows),
            "EMP_ID": emp_id,
            "BASE_AMOUNT": amount,
            "CURRENCY": CURRENCY,
            "PAY_GRADE": grade,
            "EFFECTIVE_DATE": effective,
        })


def _allowances(emp_id, batch_day, ids, rows, rng) -> None:
    for alw_type in rng.sample(ALLOWANCE_TYPES, rng.randint(1, 3)):
        rows.append({
            "ALW_ID": ids["ALLOWANCES"] + len(rows),
            "EMP_ID": emp_id,
            "ALW_TYPE": alw_type,
            "AMOUNT": Decimal(rng.randint(*ALLOWANCE_RANGES[alw_type])),
            "EFFECTIVE_DATE": batch_day,
        })


def _employee_defects(data, batch, rows, master, bad_rate, rng) -> None:
    bad = _pick_bad(len(rows), bad_rate, rng)
    bad_rows = set(bad)
    # A duplicate copies a STAFF_NO that is still unique, on a row with no other defect.
    counts = {}
    for row in data.employees:
        counts[row["STAFF_NO"]] = counts.get(row["STAFF_NO"], 0) + 1
    sources = [r["STAFF_NO"] for r in data.employees if counts[r["STAFF_NO"]] == 1 and _clean_employee(r, master)]
    sources += [r["STAFF_NO"] for i, r in enumerate(rows) if i not in bad_rows]

    for i in bad:
        row = rows[i]
        defect = rng.choice([d for d in DEFECTS["EMPLOYEES"] if sources or d != "duplicate STAFF_NO"])
        if defect == "null FULL_NAME":
            row["FULL_NAME"] = None
        elif defect == "duplicate STAFF_NO":
            row["STAFF_NO"] = sources.pop(rng.randrange(len(sources)))
        elif defect == "HIRE_DATE not YYYY-MM-DD":
            row["HIRE_DATE"] = _bad_hire_date(row["HIRE_DATE"], rng)
        elif defect == "STATUS not A/T":
            row["STATUS"] = rng.choice(BAD_STATUSES)
        elif defect == "orphan DEPT_ID":
            row["DEPT_ID"] = ORPHAN_DEPT_BASE + rng.randrange(99_999)
        else:
            row["DEPT_NAME"] = _drifted_name(row["DEPT_NAME"], master, rng)
        batch.record("EMPLOYEES", defect)


def _job_history_defects(batch, rows, bad_rate, rng) -> None:
    for i in _pick_bad(len(rows), bad_rate, rng):
        row = rows[i]
        row["END_DATE"] = row["START_DATE"] - timedelta(days=rng.randint(1, 400))
        batch.record("JOB_HISTORY", "END_DATE before START_DATE")


def _salary_defects(batch, rows, bad_rate, rng) -> None:
    for i in _pick_bad(len(rows), bad_rate, rng):
        row = rows[i]
        defect = rng.choice(list(DEFECTS["SALARIES"]))
        if defect.startswith("BASE_AMOUNT"):
            row["BASE_AMOUNT"] = rng.choice((Decimal(0), -row["BASE_AMOUNT"], row["BASE_AMOUNT"] * 1000))
        elif defect.startswith("CURRENCY"):
            row["CURRENCY"] = rng.choice(BAD_CURRENCIES)
        else:
            row["EMP_ID"] = ORPHAN_ID_BASE + rng.randrange(10_000_000)
        batch.record("SALARIES", defect)


def _allowance_defects(batch, rows, bad_rate, rng) -> None:
    for i in _pick_bad(len(rows), bad_rate, rng):
        row = rows[i]
        defect = rng.choice(list(DEFECTS["ALLOWANCES"]))
        if defect == "invalid ALW_TYPE":
            row["ALW_TYPE"] = rng.choice(BAD_ALLOWANCE_TYPES)
        else:
            row["AMOUNT"] = -row["AMOUNT"]
        batch.record("ALLOWANCES", defect)


def _clean_employee(row: dict, master: dict) -> bool:
    dept = master.get(row["DEPT_ID"])
    return (
        row["FULL_NAME"] is not None
        and row["STATUS"] in STATUSES
        and row["HIRE_DATE"] is not None
        and bool(_HIRE_DATE_PATTERN.fullmatch(row["HIRE_DATE"]))
        and dept is not None
        and dept["DEPT_NAME"] == row["DEPT_NAME"]
    )


def _bad_hire_date(iso: str, rng: Random) -> str:
    year, month, day = iso.split("-")
    return rng.choice((
        f"{day}/{month}/{year}",  # DD/MM/YYYY
        f"{year}/{month}/{day}",  # slashes
        f"{year}{month}{day}",  # no separators
        f"{day}-{date(2000, int(month), 1):%b}-{year}",  # 15-Mar-2019
        f"{year}-{int(month)}-{int(day)}",  # no zero padding
        f"{date(int(year), int(month), int(day)):%B} {int(day)}, {year}",  # March 15, 2019
    ))


def _drifted_name(name: str, master: dict, rng: Random) -> str:
    other = [d["DEPT_NAME"] for d in master.values() if d["DEPT_NAME"] != name]
    return rng.choice((
        rng.choice(other),  # moved department, copy never updated
        name.upper(),  # re-keyed in capitals
        name[:4] + ".",  # abbreviated
        name + " Dept",  # old naming
    ))


def _pick_bad(count: int, bad_rate: float, rng: Random) -> list[int]:
    return sorted(rng.sample(range(count), round(count * bad_rate)))


def _weighted(weights: dict, rng: Random):
    return rng.choices(list(weights), weights=list(weights.values()))[0]
