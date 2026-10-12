from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_oracle.default.dqlab.v_monthly_payroll/profiler/column-profile"); page.wait_for_timeout(5000)
    shot(page, "i12_colprofile")
    print([t.inner_text() for t in page.get_by_role("tab").all()][:20])
    print(" ".join(page.locator("body").inner_text().split())[:700])
    b.close()
