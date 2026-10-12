from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/data-quality/test-suites"); page.wait_for_timeout(4000)
    page.get_by_role("button", name="Add a Bundle Suite").click(); page.wait_for_timeout(1500)
    page.locator("input[id='root/name']").fill("dqlab_mysql_suite")
    page.get_by_test_id("select-all-test-cases").check(force=True); page.wait_for_timeout(500)
    sw = page.locator("input[id='root/enableScheduler']")
    page.get_by_label("Create Pipeline").check(force=True); page.wait_for_timeout(1200)
    page.locator("input[id='root/pipelineName']").fill("dqlab_mysql_suite_pipeline")
    page.get_by_text("On Demand", exact=True).click(); page.wait_for_timeout(500)
    shot(page, "i07_7_bundle_form")
    page.get_by_test_id("submit-button").click(); page.wait_for_timeout(5000)
    shot(page, "i07_8_suite_created"); print(page.url)
    b.close()
