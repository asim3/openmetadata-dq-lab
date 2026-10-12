from playwright.sync_api import sync_playwright
from common import *
URL = BASE + "/service/databaseServices/dqlab_oracle/edit-ingestion/dqlab_oracle.a8aeb513-432e-45bc-b371-74488e30cc7f/profiler"
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(URL); page.wait_for_timeout(3000)
    for t in ("ingestion-section-scope-toggle","ingestion-section-advanced-toggle"):
        page.get_by_test_id(t).click(); page.wait_for_timeout(500)
    shot(page, "i10_12_scope")
    cb = page.locator("input[id='root/includeViews']")
    print("includeViews before:", cb.is_checked())
    cb.evaluate("e=>e.closest('label').scrollIntoView()")
    page.locator("label:has(input[id='root/includeViews'])").click()
    print("includeViews after:", cb.is_checked())
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(2000)
    page.get_by_text("On Demand", exact=True).click(); page.wait_for_timeout(500)
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(6000)
    shot(page, "i10_14_submitted"); print(page.url)
    b.close()
