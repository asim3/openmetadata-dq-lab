from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/glossary/BusinessGlossary.Product"); page.wait_for_timeout(4000)
    page.get_by_role("tab", name="Activity Feeds & Tasks").click(); page.wait_for_timeout(2500)
    page.get_by_text("Tasks", exact=True).first.click(); page.wait_for_timeout(2000)
    page.get_by_test_id("workflow-task-action-primary").click(); page.wait_for_timeout(1200)
    page.locator("[role=dialog] textarea, [role=dialog] .tiptap, [role=dialog] [contenteditable=true]").first.fill("Definition agreed.") if page.locator("[role=dialog] textarea").count() else None
    page.get_by_role("button", name="Ok").click(); page.wait_for_timeout(3500)
    shot(page, "g2_9_approved")
    t=" ".join(page.locator("body").inner_text().split()); print(t[t.find("Product"):][:80])
    b.close()
