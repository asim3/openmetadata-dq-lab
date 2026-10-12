from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings"); page.wait_for_timeout(2500)
    print("settings has About:", page.get_by_text("About", exact=True).count())
    page.get_by_test_id("help-icon").click(); page.wait_for_timeout(1000)
    shot(page, "g7_1_help")
    print([" ".join(e.inner_text().split()) for e in page.locator("[role=menuitem], [class*=menu] li, [class*=dropdown] a").all() if e.is_visible()][:12])
    page.goto(BASE + "/settings/about"); page.wait_for_timeout(2500); print(page.url, " ".join(page.locator("body").inner_text().split())[100:300])
    b.close()
