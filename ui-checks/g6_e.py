from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings"); page.wait_for_timeout(2500)
    page.get_by_text("Governance", exact=True).last.click(); page.wait_for_timeout(3000)
    print(page.url, " ".join(page.locator("body").inner_text().split())[100:500])
    b.close()
