from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings/apps"); page.wait_for_timeout(4500)
    page.get_by_text("Data Insights", exact=True).first.click(); page.wait_for_timeout(3500)
    page.get_by_test_id("run-now-button").click(); page.wait_for_timeout(4000)
    shot(page, "g6_3_di_app")
    b.close()
