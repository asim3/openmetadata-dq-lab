from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings/customProperties/tables"); page.wait_for_timeout(3000)
    page.get_by_test_id("add-field-button").click(); page.wait_for_timeout(1500)
    page.locator("input[id='root/name']").fill("classificationReviewedOn")
    page.get_by_text("Select Type", exact=True).click(); page.wait_for_timeout(600)
    print("types:", [e.inner_text() for e in page.locator(".ant-select-item-option").all()][:30])
    page.keyboard.type("String"); page.wait_for_timeout(500); page.keyboard.press("Enter"); page.wait_for_timeout(500)
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Date the classification level was last reviewed.")
    shot(page, "g3_8_prop_form")
    page.get_by_role("button", name="Create").click(); page.wait_for_timeout(3000)
    b.close()
