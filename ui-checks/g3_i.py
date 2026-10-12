from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers"); page.wait_for_timeout(4000)
    page.get_by_test_id("version-button").click(); page.wait_for_timeout(3500)
    shot(page, "g3_12_versions"); print(page.url)
    t=" ".join(page.locator("body").inner_text().split()); i=t.find("Versions"); print(t[i:i+500])
    b.close()
