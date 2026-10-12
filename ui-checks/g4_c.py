from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.orders"); page.wait_for_timeout(3500)
    page.get_by_test_id("edit-retention-period-button").click(); page.wait_for_timeout(800)
    page.locator("[role=dialog] input").first.fill("P7Y")
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(2500)
    t=" ".join(page.locator("body").inner_text().split()); i=t.find("Retention Period"); print(t[i:i+60])
    b.close()
