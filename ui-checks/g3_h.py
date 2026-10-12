from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers"); page.wait_for_timeout(4000)
    page.get_by_text("Tags", exact=True).last.locator("xpath=following::*[@data-testid='edit-button'][1]").click(); page.wait_for_timeout(1000)
    shot(page, "g3_11_edit_level")
    box = page.locator("#tagsForm_tags"); box.click(); box.fill("Restricted"); page.wait_for_timeout(2000)
    page.get_by_text("Restricted", exact=True).last.click(); page.wait_for_timeout(500)
    box.fill("Secret"); page.wait_for_timeout(2000)
    page.get_by_text("Secret", exact=True).last.click(); page.wait_for_timeout(600)
    shot(page, "g3_11_edit_level")
    page.get_by_role("button", name="Update").click(); page.wait_for_timeout(2500)
    b.close()
