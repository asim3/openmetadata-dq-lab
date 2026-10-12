from playwright.sync_api import sync_playwright
from dq import *
T="dqlab_oracle.default.dqlab."
SQL = {
 "employees_dept_name_matches_master": ("EMPLOYEES", """SELECT e.EMP_ID, e.DEPT_NAME, d.DEPT_NAME AS MASTER_NAME
FROM EMPLOYEES e
JOIN DEPARTMENTS d ON d.DEPT_ID = e.DEPT_ID
WHERE e.DEPT_NAME <> d.DEPT_NAME"""),
 "job_history_end_after_start": ("JOB_HISTORY", """SELECT JH_ID, EMP_ID, START_DATE, END_DATE
FROM JOB_HISTORY
WHERE END_DATE < START_DATE"""),
 "salaries_no_orphan_emp": ("SALARIES", """SELECT s.SAL_ID, s.EMP_ID
FROM SALARIES s
LEFT JOIN EMPLOYEES e ON e.EMP_ID = s.EMP_ID
WHERE e.EMP_ID IS NULL"""),
}
with sync_playwright() as p:
    b, page = open_page(p)
    for name,(tbl,sql) in SQL.items():
        create_test(page, T+tbl, name, "Custom SQL Query", sql=sql, params={"strategy":"ROWS","operator":"<=","threshold":0})
    b.close()
