from playwright.sync_api import sync_playwright
from common import *
M="dqlab_mysql.default.dqlab."
def popup_pick(page, tid, label):
    page.get_by_test_id(tid).click(); page.wait_for_timeout(1000)
    page.get_by_text(label, exact=True).last.click(); page.wait_for_timeout(500)
    page.locator("button:has(svg)").filter(has_text="").locator("visible=true").last.click()
    page.wait_for_timeout(2500)
with sync_playwright() as p:
    b, page = open_page(p)
    for tbl in ("orders","customers"):
        page.goto(f"{BASE}/table/{M}{tbl}"); page.wait_for_timeout(3500)
        page.get_by_test_id("edit-tier").click(); page.wait_for_timeout(1000)
        page.get_by_text("Tier1", exact=True).last.click(); page.wait_for_timeout(500)
        shot(page, "g4_tier_pick")
        page.locator(".ant-popover button.ant-btn-primary, [role=dialog] button.ant-btn-primary, button.ant-btn-primary").last.click(); page.wait_for_timeout(2500)
        print("tier", tbl)
    page.goto(f"{BASE}/table/{M}customers"); page.wait_for_timeout(3500)
    page.get_by_test_id("edit-certification").click(); page.wait_for_timeout(1000)
    page.get_by_text("Gold", exact=True).last.click(); page.wait_for_timeout(500)
    page.locator("button.ant-btn-primary").last.click(); page.wait_for_timeout(2500); print("cert")
    page.goto(f"{BASE}/table/{M}orders"); page.wait_for_timeout(3500)
    page.get_by_test_id("edit-retention-period-button").click(); page.wait_for_timeout(800)
    shot(page, "g4_retention_form")
    page.keyboard.type("7 years"); page.keyboard.press("Enter"); page.wait_for_timeout(2500)
    b.close()
