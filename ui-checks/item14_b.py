from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    for path in ("/data-quality/test-cases", "/data-quality/dashboard", "/incident-manager"):
        page.goto(BASE + path); page.wait_for_timeout(4500)
        t = " ".join(page.locator("body").inner_text().split())
        print("==", path, "|", t[130:900]); shot(page, "i14_" + path.strip("/").replace("/","_"))
    b.close()
