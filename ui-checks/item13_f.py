import sys
from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/test-suites/dqlab_oracle_suite"); page.wait_for_timeout(3500)
    page.get_by_text("Pipelines", exact=False).first.click(); page.wait_for_timeout(2500)
    page.get_by_test_id("more-actions").click(); page.wait_for_timeout(700)
    page.get_by_text("Run", exact=True).first.click(); page.wait_for_timeout(2500)
    shot(page, "i13_10_ran")
    b.close()
