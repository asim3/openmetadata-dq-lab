"""Legacy HR schema for the Phase 2 Oracle source (app-user schema in XEPDB1).

Like the MySQL schema it is deliberately loose: primary keys only, no FOREIGN KEY,
UNIQUE or NOT NULL constraints, so bad rows land and OpenMetadata's tests catch
them. Identifiers are uppercase and the types are Oracle-native.

Three legacy quirks are built in (see oracle_generators.py):
- EMPLOYEES.HIRE_DATE is VARCHAR2, not DATE;
- EMPLOYEES.STATUS is CHAR(1);
- EMPLOYEES.DEPT_NAME is a copy of DEPARTMENTS.DEPT_NAME that can drift.
"""

from __future__ import annotations

SERVICE_NAME = "XEPDB1"

# Insert order; the child tables reference EMPLOYEES by convention only.
TABLES = ("DEPARTMENTS", "EMPLOYEES", "JOB_HISTORY", "SALARIES", "ALLOWANCES")
VIEWS = ("V_CURRENT_EMPLOYEES", "V_MONTHLY_PAYROLL")

COLUMNS = {
    "DEPARTMENTS": ("DEPT_ID", "DEPT_NAME", "COST_CENTER"),
    "EMPLOYEES": ("EMP_ID", "STAFF_NO", "FULL_NAME", "DEPT_ID", "DEPT_NAME", "HIRE_DATE", "JOB_TITLE", "STATUS"),
    "JOB_HISTORY": ("JH_ID", "EMP_ID", "DEPT_ID", "JOB_TITLE", "START_DATE", "END_DATE"),
    "SALARIES": ("SAL_ID", "EMP_ID", "BASE_AMOUNT", "CURRENCY", "PAY_GRADE", "EFFECTIVE_DATE"),
    "ALLOWANCES": ("ALW_ID", "EMP_ID", "ALW_TYPE", "AMOUNT", "EFFECTIVE_DATE"),
}

DDL = {
    "DEPARTMENTS": """
        CREATE TABLE DEPARTMENTS (
            DEPT_ID     NUMBER(6) PRIMARY KEY,
            DEPT_NAME   VARCHAR2(60),
            COST_CENTER VARCHAR2(10)
        )
    """,
    "EMPLOYEES": """
        CREATE TABLE EMPLOYEES (
            EMP_ID    NUMBER(10) PRIMARY KEY,
            STAFF_NO  VARCHAR2(12),
            FULL_NAME VARCHAR2(120),
            DEPT_ID   NUMBER(6),
            DEPT_NAME VARCHAR2(60),
            HIRE_DATE VARCHAR2(20),
            JOB_TITLE VARCHAR2(60),
            STATUS    CHAR(1)
        )
    """,
    "JOB_HISTORY": """
        CREATE TABLE JOB_HISTORY (
            JH_ID      NUMBER(10) PRIMARY KEY,
            EMP_ID     NUMBER(10),
            DEPT_ID    NUMBER(6),
            JOB_TITLE  VARCHAR2(60),
            START_DATE DATE,
            END_DATE   DATE
        )
    """,
    "SALARIES": """
        CREATE TABLE SALARIES (
            SAL_ID         NUMBER(10) PRIMARY KEY,
            EMP_ID         NUMBER(10),
            BASE_AMOUNT    NUMBER(12, 2),
            CURRENCY       VARCHAR2(3),
            PAY_GRADE      VARCHAR2(4),
            EFFECTIVE_DATE DATE
        )
    """,
    "ALLOWANCES": """
        CREATE TABLE ALLOWANCES (
            ALW_ID         NUMBER(10) PRIMARY KEY,
            EMP_ID         NUMBER(10),
            ALW_TYPE       VARCHAR2(16),
            AMOUNT         NUMBER(10, 2),
            EFFECTIVE_DATE DATE
        )
    """,
}

VIEW_DDL = {
    # Each employee with their latest JOB_HISTORY row.
    "V_CURRENT_EMPLOYEES": """
        CREATE OR REPLACE VIEW V_CURRENT_EMPLOYEES AS
        SELECT e.EMP_ID, e.STAFF_NO, e.FULL_NAME, e.STATUS,
               j.DEPT_ID, j.JOB_TITLE, j.START_DATE
        FROM EMPLOYEES e
        JOIN (
            SELECT jh.*, ROW_NUMBER() OVER (PARTITION BY jh.EMP_ID ORDER BY jh.START_DATE DESC, jh.JH_ID DESC) AS RN
            FROM JOB_HISTORY jh
        ) j ON j.EMP_ID = e.EMP_ID AND j.RN = 1
    """,
    # Latest base salary plus allowances per employee. The STATUS = 'A' filter
    # silently drops terminated staff and rows with a bad status ('a', blank):
    # the view's totals disagree with the raw tables, on purpose.
    "V_MONTHLY_PAYROLL": """
        CREATE OR REPLACE VIEW V_MONTHLY_PAYROLL AS
        SELECT e.EMP_ID, e.STAFF_NO, e.FULL_NAME,
               s.BASE_AMOUNT, s.CURRENCY,
               NVL(a.ALLOWANCE_TOTAL, 0) AS ALLOWANCE_TOTAL,
               s.BASE_AMOUNT + NVL(a.ALLOWANCE_TOTAL, 0) AS TOTAL_PAY
        FROM EMPLOYEES e
        JOIN (
            SELECT sa.*, ROW_NUMBER() OVER (PARTITION BY sa.EMP_ID ORDER BY sa.EFFECTIVE_DATE DESC, sa.SAL_ID DESC) AS RN
            FROM SALARIES sa
        ) s ON s.EMP_ID = e.EMP_ID AND s.RN = 1
        LEFT JOIN (
            SELECT EMP_ID, SUM(AMOUNT) AS ALLOWANCE_TOTAL FROM ALLOWANCES GROUP BY EMP_ID
        ) a ON a.EMP_ID = e.EMP_ID
        WHERE e.STATUS = 'A'
    """,
}


def existing_objects(cursor, kind: str) -> set[str]:
    cursor.execute(f"SELECT {kind}_NAME FROM USER_{kind}S")
    return {name for (name,) in cursor.fetchall()}


def create_tables(cursor) -> list[str]:
    """Create any missing tables, then (re)create the views; return the tables created."""
    before = existing_objects(cursor, "TABLE")
    created = []
    for table in TABLES:
        if table not in before:
            cursor.execute(DDL[table])
            created.append(table)
    for view in VIEWS:
        cursor.execute(VIEW_DDL[view])
    return created


def insert_sql(table: str) -> str:
    columns = COLUMNS[table]
    binds = ", ".join(f":{i}" for i in range(1, len(columns) + 1))
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({binds})"
