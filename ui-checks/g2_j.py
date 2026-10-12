from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/metrics"); page.wait_for_timeout(3500)
    page.get_by_test_id("create-metric").click(); page.wait_for_timeout(1500)
    page.locator("input[id='root/name']").fill("monthly_payroll_total"); page.locator("input[id='root/displayName']").click(); page.wait_for_timeout(800)
    t=" ".join(page.locator("body").inner_text().split()); i=t.find("Name *"); print("underscore check:", t[i:i+200])
    shot(page, "g2_15_metric_name_error")
    page.locator("input[id='root/name']").fill("monthlyPayrollTotal")
    page.locator("input[id='root/displayName']").fill("Monthly payroll total")
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Total pay for active employees in a month: base amount plus allowances.")
    for field, option in (("granularity","Month"),("metricType","Sum"),("language","SQL")):
        page.locator(f"input[id='root/{field}']").click(); page.wait_for_timeout(600)
        page.keyboard.type(option); page.wait_for_timeout(500); page.keyboard.press("Enter"); page.wait_for_timeout(400)
    page.locator("textarea").last.fill("SELECT SUM(TOTAL_PAY) FROM V_MONTHLY_PAYROLL")
    shot(page, "g2_16_metric_filled")
    page.get_by_test_id("create-button").click(); page.wait_for_timeout(3500)
    print(page.url)
    b.close()
