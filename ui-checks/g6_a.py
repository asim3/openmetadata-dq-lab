from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/data-insights/data-assets"); page.wait_for_timeout(6000)
    shot(page, "g6_1_insights"); print(page.url)
    print([" ".join(t.inner_text().split()) for t in page.get_by_role("tab").all()])
    print([(a.inner_text().strip(), a.get_attribute("href")) for a in page.locator("a:visible").all() if "insight" in (a.get_attribute("href") or "")])
    t=" ".join(page.locator("body").inner_text().split()); print(t[130:900])
    b.close()
