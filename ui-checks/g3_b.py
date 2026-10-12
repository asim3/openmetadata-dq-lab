from playwright.sync_api import sync_playwright
from common import *
TAGS = [("TopSecret","Top Secret","High impact if disclosed without authorisation."),("Secret","Secret","Medium impact if disclosed without authorisation."),("Restricted","Restricted","Low impact if disclosed without authorisation."),("Public","Public","No impact: safe to share.")]
with sync_playwright() as p:
    b, page = open_page(p)
    for name, disp, desc in TAGS:
        page.goto(BASE + "/tags/DataClassification"); page.wait_for_timeout(3000)
        (page.get_by_test_id("add-new-tag-button") if page.get_by_test_id("add-new-tag-button").count() else page.get_by_role("button", name="New Tag")).first.click(); page.wait_for_timeout(1200)
        page.locator("input[id='root/name']").fill(name); page.locator("input[id='root/displayName']").fill(disp)
        page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text(desc)
        page.get_by_role("button", name="Save").click(); page.wait_for_timeout(2500)
        print("tag", name)
    b.close()
