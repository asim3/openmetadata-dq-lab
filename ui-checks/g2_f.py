from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/glossary/BusinessGlossary.Product"); page.wait_for_timeout(9000)
    t=" ".join(page.locator("body").inner_text().split()); print(t[t.find("Product"):][:90]); print(t[t.find("Workflow History"):][:600])
    shot(page, "g2_11_product_after")
    b.close()
