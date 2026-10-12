import os
from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/glossary/BusinessGlossary"); page.wait_for_timeout(3500)
    page.get_by_role("button", name="Add term").click(); page.wait_for_timeout(1200)
    page.locator("input[id='root/name']").fill("Product")
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Something we sell, with a SKU and a price.")
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(4000)
    b.close()
    b, page = open_page(p, user="data.steward@example.com", password=os.environ["STEWARD_PW"])
    page.goto(BASE + "/glossary/BusinessGlossary.Product"); page.wait_for_timeout(5000)
    page.get_by_role("tab", name="Activity Feeds & Tasks").click(); page.wait_for_timeout(2000)
    page.get_by_text("Tasks", exact=True).first.click(); page.wait_for_timeout(2000)
    shot(page, "g2_12_steward_task")
    page.get_by_test_id("workflow-task-action-primary").click(); page.wait_for_timeout(1200)
    page.get_by_role("button", name="Ok").click(); page.wait_for_timeout(4000)
    b.close()
