from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/explore/tables"); page.wait_for_timeout(4000)
    print([(e.get_attribute("data-testid"), " ".join(e.inner_text().split())) for e in page.locator("button:visible").all() if "search-dropdown" in (e.get_attribute("data-testid") or "")])
    page.get_by_test_id("search-dropdown-Tag").click() if page.get_by_test_id("search-dropdown-Tag").count() else page.get_by_test_id("search-dropdown-Tags").click()
    page.wait_for_timeout(800); page.keyboard.type("Restricted"); page.wait_for_timeout(2000)
    page.get_by_text("DataClassification.Restricted").first.click(); page.wait_for_timeout(500)
    page.get_by_role("button", name="Update").click() if page.get_by_role("button", name="Update").count() else None
    page.wait_for_timeout(3500)
    shot(page, "g3_10_explore_filter")
    cards = page.locator("[data-testid='table-data-card'], [data-testid*='data-card']")
    print("cards:", cards.count())
    t=" ".join(page.locator("body").inner_text().split()); i=t.find("Browse"); print(t[i:i+900])
    b.close()
