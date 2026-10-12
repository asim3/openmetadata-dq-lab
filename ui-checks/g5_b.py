from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.orders"); page.wait_for_timeout(4000)
    page.get_by_test_id("request-description").first.click(); page.wait_for_timeout(1500)
    page.get_by_text("Data Governance Office", exact=True).first.locator("xpath=following-sibling::*[1]").click(); page.wait_for_timeout(500)
    box = page.locator("input[type=search], .ant-select-selection-search-input").last
    box.click(); page.keyboard.type("Data Steward"); page.wait_for_timeout(2000)
    page.get_by_text("Data Steward", exact=True).last.click(); page.wait_for_timeout(500)
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("One row per purchase: who bought which product, how many, for how much, and its status.")
    shot(page, "g5_5_request")
    page.get_by_role("button", name="Suggest").click(); page.wait_for_timeout(3500)
    print(page.url); shot(page, "g5_6_task_created")
    b.close()
