from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/data-insights/app-analytics"); page.wait_for_timeout(6000)
    shot(page, "g6_4_analytics")
    t=" ".join(page.locator("body").inner_text().split()); print("analytics:", t[130:900])
    page.goto(BASE + "/data-insights/kpi"); page.wait_for_timeout(3500)
    shot(page, "g6_5_kpi"); print(page.url)
    page.get_by_role("button", name="Add KPI").first.click(); page.wait_for_timeout(2500)
    shot(page, "g6_6_kpi_form"); print(page.url)
    print(page.evaluate("[...document.querySelectorAll('input,textarea,.tiptap,[role=combobox]')].filter(e=>e.offsetParent).map(e=>e.tagName+'|'+e.id+'|'+(e.placeholder||''))"))
    b.close()
