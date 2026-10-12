from playwright.sync_api import sync_playwright
from common import *
def set_status(page, status):
    page.get_by_text("Incident Status").locator("xpath=following::button[1]").click(); page.wait_for_timeout(800)
    page.locator("[role=dialog] .ant-select").first.click(); page.wait_for_timeout(600)
    page.locator(".ant-select-item-option").filter(has_text=status).first.click(); page.wait_for_timeout(700)
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/test-case/dqlab_mysql.default.dqlab.customers.age.customers_age_between_18_and_90"); page.wait_for_timeout(5000)
    t=" ".join(page.locator("body").inner_text().split()); i=t.find("Incident Status"); print("now:", t[i:i+60])
    set_status(page, "Assigned")
    sel = page.locator("[role=dialog] .ant-select").nth(1)
    sel.click(); page.keyboard.type("admin"); page.wait_for_timeout(1800)
    page.locator(".ant-select-item-option").filter(has_text="admin").first.click(); page.wait_for_timeout(500)
    shot(page, "i09_3_assigned_form")
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(2500)
    page.get_by_text("Severity").locator("xpath=following::button[1]").click(); page.wait_for_timeout(800)
    shot(page, "i09_4_severity")
    print([e.inner_text() for e in page.locator(".ant-select-item-option, [role=option]").all()])
    b.close()
