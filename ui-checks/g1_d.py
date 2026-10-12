from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers"); page.wait_for_timeout(4000)
    page.get_by_test_id("edit-owner").click(); page.wait_for_timeout(1000)
    page.get_by_text("Data Governance Office", exact=True).last.click(); page.wait_for_timeout(1500)
    shot(page, "g1_8_after_owner")
    print([e.get_attribute("data-testid") for e in page.locator("button:visible").all() if e.is_visible()][:40])
    page.get_by_test_id("add-domain").first.click(); page.wait_for_timeout(1000)
    shot(page, "g1_9_domain_popup")
    b.close()
