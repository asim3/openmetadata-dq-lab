from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/tags"); page.wait_for_timeout(3500)
    print([(e.get_attribute("data-testid"), " ".join(e.inner_text().split())) for e in page.locator("button:visible").all()][6:16])
    page.get_by_test_id("add-classification").click(); page.wait_for_timeout(1500)
    page.locator("input[id='root/name']").fill("DataClassification")
    page.locator("input[id='root/displayName']").fill("Data Classification")
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("NDMO data classification levels, by impact of unauthorised disclosure.")
    page.get_by_label("Mutually Exclusive").check(force=True)
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(3500)
    print(page.url); shot(page, "g3_2_class_created")
    page.get_by_test_id("add-new-tag-button").click(); page.wait_for_timeout(1500)
    shot(page, "g3_3_tag_form")
    print(page.evaluate("[...document.querySelectorAll('input,textarea,button[role=switch],.tiptap')].filter(e=>e.offsetParent).map(e=>e.tagName+'|'+e.id+'|'+(e.getAttribute('data-testid')||'')+'|'+(e.placeholder||''))"))
    b.close()
