from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    for v in ("v_current_employees", "v_monthly_payroll"):
        page.goto(f"{BASE}/table/dqlab_oracle.default.dqlab.{v}/lineage")
        page.wait_for_timeout(5000)
        shot(page, f"i11_{v}")
        nodes = [n.inner_text().split("\n")[0] for n in page.locator(".react-flow__node").all()]
        print(v, "nodes:", nodes)
    b.close()
