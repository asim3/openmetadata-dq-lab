from playwright.sync_api import sync_playwright
from common import *
TABLES = [("dqlab_mysql.default.dqlab."+n, "Commerce") for n in ("customers","orders","products")] + \
         [("dqlab_oracle.default.dqlab."+n, "Human Resources") for n in ("EMPLOYEES","DEPARTMENTS","JOB_HISTORY","SALARIES","ALLOWANCES","v_current_employees","v_monthly_payroll")]
with sync_playwright() as p:
    b, page = open_page(p)
    for fqn, dom in TABLES:
        page.goto(f"{BASE}/table/{fqn}"); page.wait_for_timeout(3500)
        hdr = " ".join(page.locator("body").inner_text().split())
        if "Data Governance Office" not in hdr[:600]:
            page.get_by_test_id("edit-owner").click(); page.wait_for_timeout(800)
            page.get_by_text("Data Governance Office", exact=True).last.click(); page.wait_for_timeout(1500)
        page.get_by_test_id("add-domain").first.click(); page.wait_for_timeout(800)
        page.get_by_text(dom, exact=True).last.click(); page.wait_for_timeout(1500)
        print("done", fqn.split(".")[-1])
    b.close()
