from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/glossary/BusinessGlossary.Customer"); page.wait_for_timeout(4000)
    page.get_by_role("tab", name="Assets").click(); page.wait_for_timeout(2500)
    t=" ".join(page.locator("body").inner_text().split()); print("assets tab:", t[t.find("Assets"):][:160])
    page.goto(BASE + "/metrics"); page.wait_for_timeout(3500)
    print([(e.get_attribute("data-testid"), " ".join(e.inner_text().split())) for e in page.locator("button:visible").all()][6:14])
    page.get_by_test_id("create-metric").click() if page.get_by_test_id("create-metric").count() else page.get_by_role("button", name="Add Metric").click()
    page.wait_for_timeout(1500); shot(page, "g2_14_metric_form")
    print(page.evaluate("[...document.querySelectorAll('input,textarea,[contenteditable=true]')].filter(e=>e.offsetParent).map(e=>e.tagName+'|'+e.id+'|'+(e.placeholder||''))"))
    b.close()
