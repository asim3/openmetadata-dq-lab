from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    for name, fqn in (("status","dqlab_oracle.default.dqlab.EMPLOYEES.status.employees_status_allowed"),("orphan","dqlab_oracle.default.dqlab.EMPLOYEES.employees_no_orphan_dept")):
        page.goto(f"{BASE}/test-case/{fqn}"); page.wait_for_timeout(5000)
        shot(page, f"i14_case_{name}")
        print(name, [t.inner_text().replace("\n"," ") for t in page.get_by_role("tab").all()], "|", " ".join(page.locator("body").inner_text().split())[200:600])
    b.close()
