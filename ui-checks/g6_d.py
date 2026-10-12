from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/data-insights/kpi/add-kpi"); page.wait_for_timeout(3500)
    page.locator("#chartType").click(); page.wait_for_timeout(1000)
    print("charts:", [" ".join(e.inner_text().split()) for e in page.locator(".ant-select-item-option, [role=option]").all()])
    page.get_by_text("Description KPI", exact=True).last.click(); page.wait_for_timeout(600)
    page.locator("#displayName").fill("Description coverage")
    page.locator("#targetValue").fill("80") if page.locator("#targetValue").count() else None
    page.locator("#startDate").click(); page.keyboard.type("2026-10-12"); page.keyboard.press("Enter")
    page.locator("#endDate").click(); page.keyboard.type("2026-12-31"); page.keyboard.press("Enter")
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Share of data assets that have a description: target 80%.")
    shot(page, "g6_7_kpi_filled")
    page.mouse.wheel(0,3000); page.wait_for_timeout(600)
    print(page.evaluate("[...document.querySelectorAll('button')].filter(e=>e.offsetParent).map(e=>(e.getAttribute('data-testid')||'')+'|'+e.innerText.trim()).slice(-5)"))
    page.get_by_test_id("submit-btn").click() if page.get_by_test_id("submit-btn").count() else page.get_by_role("button", name="Save").last.click()
    page.wait_for_timeout(3500)
    print(page.url); shot(page, "g6_8_kpi_saved")
    b.close()
