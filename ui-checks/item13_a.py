from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_oracle.default.dqlab.EMPLOYEES/profiler/data-quality"); page.wait_for_timeout(4000)
    shot(page, "i13_1_dq")
    page.get_by_role("button", name="Add").click(); page.wait_for_timeout(700)
    page.get_by_text("Test case", exact=True).click(); page.wait_for_timeout(1500)
    page.get_by_text("Column Level").first.click(); page.wait_for_timeout(800)
    shot(page, "i13_4_col")
    print([ (e.get_attribute("data-testid"), e.get_attribute("id"), e.get_attribute("placeholder")) for e in page.query_selector_all("input")][-12:])
    b.close()
