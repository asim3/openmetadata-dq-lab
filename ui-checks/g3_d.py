from playwright.sync_api import sync_playwright
from common import *
T = [("dqlab_mysql.default.dqlab.products","Public"),("dqlab_mysql.default.dqlab.customers","Restricted"),("dqlab_oracle.default.dqlab.EMPLOYEES","Restricted"),("dqlab_oracle.default.dqlab.SALARIES","Restricted")]
with sync_playwright() as p:
    b, page = open_page(p)
    for fq, tag in T:
        page.goto(f"{BASE}/table/{fq}"); page.wait_for_timeout(4000)
        page.get_by_text("Tags", exact=True).last.locator("xpath=following::*[@data-testid='add-tag'][1]").click()
        page.wait_for_timeout(1000)
        box = page.locator("#tagsForm_tags"); box.click(); box.fill(tag); page.wait_for_timeout(2000)
        page.get_by_text(tag, exact=True).last.click(); page.wait_for_timeout(500)
        page.get_by_role("button", name="Update").click() if page.get_by_role("button", name="Update").count() else page.get_by_test_id("saveAssociatedTag").click()
        page.wait_for_timeout(2500); print("tagged", fq.split(".")[-1], tag)
    b.close()
