from playwright.sync_api import sync_playwright
from common import *
def set_status(page, status):
    page.get_by_text("Incident Status").locator("xpath=following::button[1]").click(); page.wait_for_timeout(800)
    page.locator("[role=dialog] .ant-select").first.click(); page.wait_for_timeout(600)
    page.locator(".ant-select-item-option").filter(has_text=status).first.click(); page.wait_for_timeout(700)
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/test-case/dqlab_mysql.default.dqlab.customers.age.customers_age_between_18_and_90"); page.wait_for_timeout(5000)
    set_status(page, "Resolved")
    shot(page, "i09_5_resolved_form")
    print(page.evaluate("[...document.querySelectorAll('[role=dialog] label, [role=dialog] .ant-select, [role=dialog] textarea, [role=dialog] .tiptap, [role=dialog] input')].map(e=>e.tagName+'|'+(e.innerText||e.placeholder||'').slice(0,40))"))
    b.close()
