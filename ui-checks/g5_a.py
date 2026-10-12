from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers"); page.wait_for_timeout(4000)
    page.get_by_test_id("manage-button").click(); page.wait_for_timeout(800)
    page.get_by_text("Announcements", exact=True).click(); page.wait_for_timeout(1200)
    page.get_by_test_id("add-announcement").click(); page.wait_for_timeout(1200)
    page.locator("#title").fill("Customers is now classified Secret")
    page.locator("#startTime").click(); page.keyboard.type("2026-10-12"); page.keyboard.press("Enter"); page.wait_for_timeout(500)
    page.locator("#endTime").click(); page.keyboard.type("2026-10-19"); page.keyboard.press("Enter"); page.wait_for_timeout(500)
    page.locator("[role=dialog] .tiptap[contenteditable=true], .ant-modal .tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Treat customers as Secret from today.")
    shot(page, "g5_3_ann_form")
    page.get_by_role("button", name="Submit").click(); page.wait_for_timeout(3000)
    shot(page, "g5_4_ann_done")
    t=" ".join(page.locator("body").inner_text().split()); print(t[t.find("Announcements"):][:300])
    b.close()
